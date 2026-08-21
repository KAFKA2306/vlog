import argparse
import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from vlog_capture.domain.error_events import ErrorEvent, ErrorKind, ErrorStage
from vlog_capture.domain.harness import TaskWeight
from vlog_capture.infrastructure.ai import (
    ImageGenerator,
    JulesClient,
    Novelizer,
    Summarizer,
)
from vlog_capture.infrastructure.daily_state import DailyStateStore
from vlog_capture.infrastructure.error_log import ErrorLogRepository
from vlog_capture.infrastructure.graph_storage import GraphStorage
from vlog_capture.infrastructure.harness import ZeroTrustHarness
from vlog_capture.infrastructure.repositories import (
    FileRepository,
    SupabaseRepository,
    TaskRepository,
)
from vlog_capture.infrastructure.settings import settings
from vlog_capture.infrastructure.system import (
    AudioRecorder,
    Transcriber,
    TranscriptPreprocessor,
)
from vlog_capture.portability import runtime_directories
from vlog_capture.secure_handlers import cmd_sync as _cmd_strict_sync
from vlog_capture.use_cases.build_novel import BuildNovelUseCase
from vlog_capture.use_cases.daily_artifacts import DailyArtifactManager
from vlog_capture.use_cases.daily_workload import (
    collect_daily_workload,
    render_daily_workload,
)
from vlog_capture.use_cases.extract_graph import ExtractGraphUseCase
from vlog_capture.use_cases.process_recording import ProcessRecordingUseCase


def _harness_run(
    task_name: str, weight: TaskWeight, func: Any, *args: Any, **kwargs: Any
) -> Any:
    return ZeroTrustHarness().run(task_name, weight, func, *args, **kwargs)


def cmd_record(args: argparse.Namespace) -> None:
    del args
    import time

    recorder = AudioRecorder()
    path = recorder.start()
    print(f"Recording: {path}")
    print("Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        files = recorder.stop() if recorder.is_recording else None
    if files:
        for saved in files:
            print(f"Saved: {saved}")


def cmd_process(args: argparse.Namespace) -> None:
    requested_sync = args.sync
    args.sync = False
    _harness_run("process", TaskWeight.HEAVY, _cmd_process_logic, args)
    if requested_sync:
        _cmd_strict_sync(args)


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
        repo.add(JulesClient().parse_task(args.content))
    elif args.action == "list":
        repo.list_pending()
    elif args.action == "done":
        repo.complete(args.content)


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


def _cmd_daily_logic(args: object) -> None:
    plan = collect_daily_workload()
    print(render_daily_workload(plan))

    if plan.counts.recordings_pending == 0 or plan.can_autorun_recording_flow:
        _harness_run(
            "daily_recording_flow",
            TaskWeight.HEAVY,
            _cmd_pending_logic,
            args,
            sync=False,
        )
    else:
        print("  recording_flow=paused waiting for VRChat/GPU/CPU headroom")

    from vlog_capture.use_cases.evaluate import EvaluateDailyContentUseCase

    if plan.counts.novel_days_pending > 0:
        evaluator = EvaluateDailyContentUseCase()
        for date_str in _collect_pending_evaluation_dates(limit=plan.next_action_limit):
            evaluator.execute(date_str, sync=False)

    _run_daily_postprocessing()


def _collect_pending_evaluation_dates(limit: int | None = None) -> list[str]:
    summary_dir = settings.summary_dir
    novel_dir = settings.novel_out_dir
    evaluation_dir = runtime_directories().data / "evaluations"

    summary_dates = {
        match.group(1)
        for path in summary_dir.glob("*_summary.txt")
        if (match := re.search(r"(\d{8})", path.stem))
    }
    novel_dates = {
        match.group(1)
        for path in novel_dir.glob("*.md")
        if (match := re.search(r"(\d{8})", path.stem))
    }
    evaluation_dates = {
        match.group(1)
        for path in evaluation_dir.glob("*.json")
        if (match := re.search(r"(\d{8})", path.stem))
    }

    pending_dates = sorted((summary_dates & novel_dates) - evaluation_dates)
    return pending_dates[:limit] if limit is not None else pending_dates


def cmd_pending(args: argparse.Namespace) -> None:
    _harness_run("pending_all", TaskWeight.HEAVY, _cmd_pending_logic, args, sync=False)
    _cmd_strict_sync(args)


def _cmd_pending_logic(args: argparse.Namespace, sync: bool = True) -> None:
    transcript_dir = settings.transcript_dir
    summary_dir = settings.summary_dir
    recording_dir = settings.recording_dir
    file_repo = FileRepository()
    manager = DailyArtifactManager(DailyStateStore())

    pending_transcription = [
        path
        for path in recording_dir.glob("*")
        if path.suffix.lower() in [".wav", ".flac", ".mp3"]
        and not (transcript_dir / f"{path.stem}.txt").exists()
    ]
    if pending_transcription:
        transcriber = Transcriber()
        preprocessor = TranscriptPreprocessor()
        for audio_path in pending_transcription:
            transcript, saved_path = transcriber.transcribe_and_save(str(audio_path))
            cleaned = preprocessor.process(transcript)
            cleaned_path = str(
                Path(saved_path).with_name(f"cleaned_{Path(saved_path).name}")
            )
            file_repo.save_text(cleaned_path, cleaned)
        transcriber.unload()

    dates = sorted(
        {
            match.group(1)
            for path in transcript_dir.glob("*.txt")
            if (match := re.search(r"(\d{8})", path.stem))
        }
        | {
            match.group(1)
            for path in summary_dir.glob("*_summary.txt")
            if (match := re.search(r"(\d{8})", path.stem))
        }
    )

    summarizer = Summarizer()
    for date_str in dates:
        files = manager.summary_sources_for_date(date_str)
        manager.refresh_summary(date_str, summarizer, file_repo, source_paths=files)

    import time

    graph_storage = GraphStorage(runtime_directories().cache / "graph" / "graph.jsonl")
    extractor = ExtractGraphUseCase(graph_storage)
    for date_str in dates:
        summary_path = summary_dir / f"{date_str}_summary.txt"
        if summary_path.exists() and extractor.execute(summary_path) > 0:
            time.sleep(4)

    use_case = BuildNovelUseCase(Novelizer(), ImageGenerator(), graph_storage)
    for date_str in dates:
        if (summary_dir / f"{date_str}_summary.txt").exists():
            use_case.execute(date_str)

    if sync:
        SupabaseRepository().sync()


def cmd_curator(args: argparse.Namespace) -> None:
    from vlog_capture.use_cases.evaluate import EvaluateDailyContentUseCase

    _harness_run(
        "curator", TaskWeight.LIGHT, EvaluateDailyContentUseCase().execute, args.date
    )


def _run_daily_postprocessing() -> None:
    _best_effort("cognee:ingest", _run_cognee_ingest)
    _best_effort("sync", SupabaseRepository().sync)
    _best_effort("notify", _send_daily_notification)


def _run_cognee_ingest() -> None:
    from scripts.ingest_to_cognee import main as ingest_to_cognee_main

    asyncio.run(ingest_to_cognee_main())


def _send_daily_notification() -> None:
    from vlog_capture.infrastructure.discord import DiscordClient

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
    from vlog_capture.use_cases.build_manga import build_manga

    _harness_run("manga", TaskWeight.LIGHT, build_manga, args.novel_file)


def cmd_error(args: argparse.Namespace) -> None:
    repository = ErrorLogRepository()
    if args.action == "record":
        repository.append(
            ErrorEvent(
                timestamp=datetime.now(),
                stage=ErrorStage(args.stage),
                kind=ErrorKind(args.kind),
                task_name=args.task_name,
                reason=args.reason,
                recording_path=args.recording_path,
            )
        )
        return

    events = repository.recent(args.days)
    print(f"error_events={len(events)} days={args.days}")
    for event in events:
        recording = f" recording={event.recording_path}" if event.recording_path else ""
        print(
            f"{event.timestamp.isoformat()} stage={event.stage.value} "
            f"kind={event.kind.value} task={event.task_name} "
            f"reason={event.reason}{recording}"
        )
