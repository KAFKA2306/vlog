import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from src.domain.audit import AuditState
from src.domain.harness import TaskWeight
from src.infrastructure.ai import ImageGenerator, JulesClient, Novelizer, Summarizer
from src.infrastructure.audit import StrictAuditor
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
    if getattr(args, "date", None):
        transcript_dir = Path("data/transcripts")
        files = sorted(
            list(transcript_dir.glob(f"cleaned_{args.date}_*.txt"))
        ) or sorted(list(transcript_dir.glob(f"{args.date}_*.txt")))
        combined_text = "".join(
            [f"\n\n--- {f.name} ---\n{file_repo.read(str(f))}" for f in files]
        )
        summary = summarizer.summarize(combined_text, date_str=args.date)
        file_repo.save_summary(summary, args.date)
    elif args.file:
        input_path = Path(args.file)
        transcript_text = file_repo.read(str(input_path))
        stem = input_path.stem
        match = re.search(r"(\d{8})", stem)
        date_str = match.group(1) if match else stem.split("_")[0]
        summary = summarizer.summarize(transcript_text, date_str=date_str)
        file_repo.save_summary(summary, date_str)


def cmd_pending(args: argparse.Namespace) -> None:
    _harness_run("pending_all", TaskWeight.HEAVY, _cmd_pending_logic, args)


def _cmd_pending_logic(args: argparse.Namespace) -> None:
    transcript_dir = Path("data/transcripts")
    summary_dir = Path("data/summaries")
    novel_dir = Path("data/novels")
    recording_dir = Path("data/recordings")
    file_repo = FileRepository()
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
    for d in [dt for dt in dates if not (summary_dir / f"{dt}_summary.txt").exists()]:
        files = sorted(list(transcript_dir.glob(f"cleaned_{d}_*.txt"))) or sorted(
            list(transcript_dir.glob(f"{d}_*.txt"))
        )
        summary = summarizer.summarize(
            "".join([f"\n\n- {f.name} -\n{file_repo.read(str(f))}" for f in files]),
            date_str=d,
        )
        file_repo.save_summary(summary, d)
    import time

    graph_storage = GraphStorage(Path("data/graph.jsonl"))
    extractor = ExtractGraphUseCase(graph_storage)
    for d in dates:
        summary_p = summary_dir / f"{d}_summary.txt"
        if summary_p.exists():
            if extractor.execute(summary_p) > 0:
                time.sleep(4)  # Avoid rate limit (15 RPM)

    use_case = BuildNovelUseCase(Novelizer(), ImageGenerator(), graph_storage)
    for d in [
        dt
        for dt in dates
        if not (novel_dir / f"{dt}.md").exists()
        and (summary_dir / f"{dt}_summary.txt").exists()
    ]:
        use_case.execute(d)
    SupabaseRepository().sync()


def cmd_curator(args: argparse.Namespace) -> None:
    from src.use_cases.evaluate import EvaluateDailyContentUseCase

    _harness_run(
        "curator", TaskWeight.LIGHT, EvaluateDailyContentUseCase().execute, args.date
    )


def cmd_notify(args: argparse.Namespace) -> None:
    from src.infrastructure.discord import DiscordClient

    DiscordClient().send_message(args.message)


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
