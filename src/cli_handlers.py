import argparse
import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from src.domain.audit import AuditState
from src.domain.harness import TaskWeight
from src.infrastructure.ai import ImageGenerator, JulesClient, Novelizer, Summarizer
from src.infrastructure.audit import StrictAuditor
from src.infrastructure.daily_state import DailyStateStore
from src.infrastructure.graph_storage import GraphStorage
from src.infrastructure.harness import ZeroTrustHarness
from src.infrastructure.repositories import (
    FileRepository,
    SupabaseRepository,
    TaskRepository,
)
from src.infrastructure.system import (
    ProcessMonitor,
    Transcriber,
    TranscriptPreprocessor,
)
from src.use_cases.build_novel import BuildNovelUseCase
from src.use_cases.daily_artifacts import DailyArtifactManager
from src.use_cases.daily_workload import collect_daily_workload, render_daily_workload
from src.use_cases.extract_graph import ExtractGraphUseCase
from src.use_cases.process_recording import ProcessRecordingUseCase


def _harness_run(
    task_name: str, weight: TaskWeight, func: Any, *args: Any, **kwargs: Any
) -> Any:
    return ZeroTrustHarness().run(task_name, weight, func, *args, **kwargs)


def _guard_vrc_running() -> None:
    safe, reason = ZeroTrustHarness().guard.check_safety(TaskWeight.HEAVY)
    if not safe:
        print(f"⚠️ {reason}. Skipping heavy processing.")
        import sys

        sys.exit(0)


def cmd_process(args: argparse.Namespace) -> None:
    _harness_run("process", TaskWeight.HEAVY, _cmd_process_logic, args)


def _cmd_process_logic(args: argparse.Namespace) -> None:
    use_case = ProcessRecordingUseCase(
        transcriber=Transcriber(),
        preprocessor=TranscriptPreprocessor(),
        summarizer=Summarizer(),
        storage=SupabaseRepository(),
        file_repository=FileRepository(),
        novelizer=Novelizer(),
        image_generator=ImageGenerator(),
    )
    use_case.execute(args.file, sync=args.sync)


def cmd_novel(args: argparse.Namespace) -> None:
    _harness_run("novel", TaskWeight.HEAVY, _cmd_novel_logic, args)


def _cmd_novel_logic(args: argparse.Namespace) -> None:
    graph_storage = GraphStorage(Path("data/graph.jsonl"))
    use_case = BuildNovelUseCase(Novelizer(), ImageGenerator(), graph_storage)
    use_case.execute(args.date)
    SupabaseRepository().sync()


def cmd_sync(args: argparse.Namespace) -> None:
    _harness_run("sync", TaskWeight.LIGHT, SupabaseRepository().sync)


def cmd_image_generate(args: argparse.Namespace) -> None:
    _harness_run("image_generate", TaskWeight.HEAVY, _cmd_image_generate_logic, args)


def _cmd_image_generate_logic(args: argparse.Namespace) -> None:
    novel_path = Path(args.novel_file)
    novel_content = novel_path.read_text(encoding="utf-8")
    output_path = (
        Path(args.output_file)
        if args.output_file
        else novel_path.parent / (novel_path.stem + ".png")
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ImageGenerator().generate_from_novel(novel_content, output_path)


def cmd_jules(args: argparse.Namespace) -> None:
    _harness_run("jules", TaskWeight.LIGHT, _cmd_jules_logic, args)


def _cmd_jules_logic(args: argparse.Namespace) -> None:
    repo = TaskRepository()
    if args.action == "add":
        task_data = JulesClient().parse_task(args.content)
        repo.add(task_data)
    elif args.action == "list":
        repo.list_pending()
    elif args.action == "done":
        repo.complete(args.task_id)


def cmd_transcribe(args: argparse.Namespace) -> None:
    _harness_run(
        "transcribe", TaskWeight.HEAVY, Transcriber().transcribe_and_save, args.file
    )


def cmd_summarize(args: argparse.Namespace) -> None:
    _harness_run("summarize", TaskWeight.LIGHT, _cmd_summarize_logic, args)


def _cmd_summarize_logic(args: argparse.Namespace) -> None:
    file_repo = FileRepository()
    summarizer = Summarizer()
    manager = DailyArtifactManager(DailyStateStore())
    if getattr(args, "date", None):
        files = manager.summary_sources_for_date(args.date)
        manager.refresh_summary(args.date, summarizer, file_repo, source_paths=files)
    elif args.file:
        input_path = Path(args.file)
        stem = input_path.stem
        match = re.search(r"(\d{8})", stem)
        date_str = match.group(1) if match else stem.split("_")[0]
        manager.refresh_summary(
            date_str,
            summarizer,
            file_repo,
            source_paths=(input_path,),
            fallback_text=file_repo.read(str(input_path)),
        )


def cmd_daily(args: argparse.Namespace) -> None:
    _harness_run("daily", TaskWeight.LIGHT, _cmd_daily_logic, args)


def _cmd_daily_logic(args: argparse.Namespace) -> None:
    plan = collect_daily_workload()
    print(render_daily_workload(plan))

    if plan.counts.recordings_pending > 0:
        if not plan.can_autorun_recording_flow:
            print("  recording_flow=paused waiting for VRChat/GPU/CPU headroom")
        else:
            _harness_run(
                "daily_recording_flow",
                TaskWeight.HEAVY,
                _cmd_pending_logic,
                args,
                sync=False,
            )
    else:
        _harness_run(
            "daily_recording_flow",
            TaskWeight.HEAVY,
            _cmd_pending_logic,
            args,
            sync=False,
        )

    from src.use_cases.evaluate import EvaluateDailyContentUseCase

    if plan.counts.novel_days_pending > 0:
        pending_evaluations = _collect_pending_evaluation_dates(
            limit=plan.next_action_limit
        )
        evaluator = EvaluateDailyContentUseCase()
        for date_str in pending_evaluations:
            evaluator.execute(date_str, sync=False)

    _run_daily_postprocessing()


def _collect_pending_evaluation_dates(limit: int | None = None) -> list[str]:
    summary_dir = Path("data/summaries")
    novel_dir = Path("data/novels")
    evaluation_dir = summary_dir.parent / "evaluations"

    summary_dates = {
        re.search(r"(\d{8})", f.stem).group(1)
        for f in summary_dir.glob("*_summary.txt")
        if re.search(r"(\d{8})", f.stem)
    }
    novel_dates = {
        re.search(r"(\d{8})", f.stem).group(1)
        for f in novel_dir.glob("*.md")
        if re.search(r"(\d{8})", f.stem)
    }
    evaluation_dates = {
        re.search(r"(\d{8})", f.stem).group(1)
        for f in evaluation_dir.glob("*.json")
        if re.search(r"(\d{8})", f.stem)
    }

    pending_dates = sorted((summary_dates & novel_dates) - evaluation_dates)
    return pending_dates[:limit] if limit is not None else pending_dates


def cmd_pending(args: argparse.Namespace) -> None:
    _harness_run("pending_all", TaskWeight.HEAVY, _cmd_pending_logic, args)


def _cmd_pending_logic(args: argparse.Namespace, sync: bool = True) -> None:
    transcript_dir = Path("data/transcripts")
    summary_dir = Path("data/summaries")
    recording_dir = Path("data/recordings")
    file_repo = FileRepository()
    manager = DailyArtifactManager(DailyStateStore())
    pending_transcription = [
        f
        for f in recording_dir.glob("*")
        if f.suffix.lower() in [".wav", ".flac", ".mp3"]
        and not (transcript_dir / f"{f.stem}.txt").exists()
    ]
    if pending_transcription:
        transcriber = Transcriber()
        preprocessor = TranscriptPreprocessor()
        for audio_path in pending_transcription:
            transcript, saved_p = transcriber.transcribe_and_save(str(audio_path))
            cleaned = preprocessor.process(transcript)
            cleaned_p = str(Path(saved_p).with_name(f"cleaned_{Path(saved_p).name}"))
            file_repo.save_text(cleaned_p, cleaned)
        transcriber.unload()
    dates = sorted(
        {
            re.search(r"(\d{8})", f.stem).group(1)
            for f in transcript_dir.glob("*.txt")
            if re.search(r"(\d{8})", f.stem)
        }
        | {
            re.search(r"(\d{8})", f.stem).group(1)
            for f in summary_dir.glob("*_summary.txt")
            if re.search(r"(\d{8})", f.stem)
        }
    )
    summarizer = Summarizer()
    for d in dates:
        files = manager.summary_sources_for_date(d)
        manager.refresh_summary(d, summarizer, file_repo, source_paths=files)
    import time

    graph_storage = GraphStorage(Path("data/graph.jsonl"))
    extractor = ExtractGraphUseCase(graph_storage)
    for d in dates:
        summary_p = summary_dir / f"{d}_summary.txt"
        if summary_p.exists():
            if extractor.execute(summary_p) > 0:
                time.sleep(4)  # Avoid rate limit (15 RPM)

    use_case = BuildNovelUseCase(Novelizer(), ImageGenerator(), graph_storage)
    for d in dates:
        if (summary_dir / f"{d}_summary.txt").exists():
            use_case.execute(d)
    if sync:
        SupabaseRepository().sync()


def cmd_curator(args: argparse.Namespace) -> None:
    from src.use_cases.evaluate import EvaluateDailyContentUseCase

    _harness_run(
        "curator", TaskWeight.LIGHT, EvaluateDailyContentUseCase().execute, args.date
    )


def cmd_notify(args: argparse.Namespace) -> None:
    from src.infrastructure.discord import DiscordClient

    DiscordClient().send_message(args.message)


def _run_daily_postprocessing() -> None:
    _best_effort("cognee:init", _run_cognee_init)
    _best_effort("cognee:ingest", _run_cognee_ingest)
    _best_effort("sync", SupabaseRepository().sync)
    _best_effort("notify", _send_daily_notification)


def _run_cognee_init() -> None:
    from scripts.init_cognee_queue import main as init_cognee_queue_main

    init_cognee_queue_main()


def _run_cognee_ingest() -> None:
    from scripts.ingest_to_cognee import main as ingest_to_cognee_main

    asyncio.run(ingest_to_cognee_main())


def _send_daily_notification() -> None:
    from src.infrastructure.discord import DiscordClient

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    DiscordClient().send_message(
        "✅ 日次処理が完了しました（"
        f"{timestamp}）\n"
        "🌐 Reader: https://kaflog.vercel.app"
    )


def _best_effort(label: str, func: Any, *args: Any, **kwargs: Any) -> None:
    try:
        func(*args, **kwargs)
    except Exception as exc:
        print(f"⚠️ {label} failed ({exc}). Continuing anyway.")


def cmd_manga(args: argparse.Namespace) -> None:
    from src.use_cases.build_manga import build_manga

    _harness_run("manga", TaskWeight.LIGHT, build_manga, args.novel_file)


def cmd_check_vrc(args: argparse.Namespace) -> None:
    if ProcessMonitor().is_running():
        sys.exit(1)


def cmd_audit(args: argparse.Namespace) -> None:
    report = StrictAuditor(
        recent_limit=args.recent,
        trace_window_minutes=args.trace_window_minutes,
    ).run()

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_audit_report(report)

    if args.strict and report.has_blockers:
        sys.exit(1)


def _print_audit_report(report) -> None:
    counts = {
        state: 0
        for state in (
            AuditState.PASS,
            AuditState.FAIL,
            AuditState.UNVERIFIED,
            AuditState.NOT_APPLICABLE,
        )
    }
    for finding in report.findings:
        counts[finding.state] += 1
        details = f" | {finding.details}" if finding.details else ""
        print(
            f"{finding.state.value.upper():13} {finding.check_name} :: "
            f"{finding.evidence}{details}"
        )

    print(
        "SUMMARY        "
        f"pass={counts[AuditState.PASS]} "
        f"fail={counts[AuditState.FAIL]} "
        f"unverified={counts[AuditState.UNVERIFIED]} "
        f"n/a={counts[AuditState.NOT_APPLICABLE]}"
    )
