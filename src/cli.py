import argparse
import re
from pathlib import Path

from src.infrastructure.ai import ImageGenerator, Summarizer
from src.infrastructure.repositories import (
    FileRepository,
    SupabaseRepository,
    TaskRepository,
)
from src.infrastructure.system import Transcriber, TranscriptPreprocessor
from src.use_cases.build_novel import BuildNovelUseCase
from src.use_cases.process_recording import ProcessRecordingUseCase


def cmd_process(args):
    from datetime import datetime

    path = Path(args.file)
    match = re.search(r"(\d{8}_\d{6})", path.name)
    start_time = (
        datetime.strptime(match.group(1), "%Y%m%d_%H%M%S")
        if match
        else datetime.now()
    )
    use_case = ProcessRecordingUseCase(
        transcriber=Transcriber(),
        preprocessor=TranscriptPreprocessor(),
        summarizer=Summarizer(),
        storage=SupabaseRepository(),
        file_repository=FileRepository(),
        diarizer=None,
    )
    from src.models import RecordingSession

    use_case.execute_session(
        RecordingSession(start_time=start_time, file_paths=(str(path),))
    )


def cmd_novel(args):
    use_case = BuildNovelUseCase(Summarizer(), ImageGenerator())
    use_case.execute(args.date)
    SupabaseRepository().sync()


def cmd_sync(args):
    SupabaseRepository().sync()


def cmd_image_generate(args):
    novel_path = Path(args.novel_file)
    content = novel_path.read_text(encoding="utf-8")
    output_path = (
        Path(args.output_file)
        if args.output_file
        else novel_path.parent / (novel_path.stem + ".png")
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ImageGenerator().generate_from_novel(content, output_path)


def cmd_jules(args):
    repo = TaskRepository()
    if args.action == "add":
        from src.infrastructure.ai import JulesClient

        repo.add(JulesClient().parse_task(args.content))
    elif args.action == "list":
        for t in repo.list_pending():
            print(f"- [{t['id'][:8]}] {t['title']}")
    elif args.action == "done":
        repo.complete(args.task_id)


def cmd_transcribe(args):
    Transcriber().transcribe_and_save(args.file)


def cmd_summarize(args):
    file_repo = FileRepository()
    summarizer = Summarizer()
    if args.date:
        transcript_dir = Path("data/transcripts")
        files = sorted(
            list(transcript_dir.glob(f"cleaned_{args.date}_*.txt"))
        ) or sorted(list(transcript_dir.glob(f"{args.date}_*.txt")))
        combined_text = "\n\n".join(file_repo.read(str(f)) for f in files)
        file_repo.save_summary(
            summarizer.generate_novel(combined_text, args.date), args.date
        )
    elif args.file:
        text = file_repo.read(args.file)
        date_str = Path(args.file).stem[:8]
        file_repo.save_summary(summarizer.generate_novel(text, date_str), date_str)


def cmd_pending(args):
    transcript_dir, summary_dir, novel_dir, recording_dir = (
        Path("data/transcripts"),
        Path("data/summaries"),
        Path("data/novels"),
        Path("data/recordings"),
    )
    file_repo = FileRepository()
    for f in recording_dir.glob("*"):
        if (
            f.suffix.lower() in [".wav", ".flac", ".mp3"]
            and not (transcript_dir / f"{f.stem}.txt").exists()
        ):
            t, p = Transcriber().transcribe_and_save(str(f))
            file_repo.save_text(
                str(Path(p).with_name(f"cleaned_{Path(p).name}")),
                TranscriptPreprocessor().process(t),
            )

    dates = sorted(
        {
            match.group(1)
            for f in transcript_dir.glob("*.txt")
            if (match := re.search(r"(\d{8})", f.stem))
        }
    )
    summarizer = Summarizer()
    for d in dates:
        if not (summary_dir / f"{d}_summary.txt").exists():
            files = sorted(list(transcript_dir.glob(f"cleaned_{d}_*.txt"))) or sorted(
                list(transcript_dir.glob(f"{d}_*.txt"))
            )
            file_repo.save_summary(
                summarizer.generate_novel(
                    "\n\n".join(file_repo.read(str(f)) for f in files), d
                ),
                d,
            )
        if not (novel_dir / f"{d}.md").exists():
            BuildNovelUseCase(Summarizer(), ImageGenerator()).execute(d)
    SupabaseRepository().sync()


def main():
    from src.main import setup_logging

    setup_logging()

    parser = argparse.ArgumentParser(description="VLog CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    p_process = subparsers.add_parser("process", help="Process audio file")
    p_process.add_argument("--file", help="Path to audio file")
    p_novel = subparsers.add_parser("novel", help="Generate novel chapter")
    p_novel.add_argument("--date", help="Target date (YYYYMMDD)")
    subparsers.add_parser("sync", help="Sync data to Supabase")
    p_img = subparsers.add_parser("image-generate", help="Generate image")
    p_img.add_argument("--novel-file", required=True)
    p_img.add_argument("--output-file")
    p_trans = subparsers.add_parser("transcribe", help="Transcribe")
    p_trans.add_argument("--file", required=True)
    p_sum = subparsers.add_parser("summarize", help="Summarize")
    p_sum.add_argument("--file")
    p_sum.add_argument("--date")
    subparsers.add_parser("pending", help="Process pending")
    p_jules = subparsers.add_parser("jules", help="Jules tasks")
    p_jules.add_argument("action", choices=["add", "list", "done"])
    p_jules.add_argument("content", nargs="?")
    p_cur = subparsers.add_parser("curator", help="Curator")
    p_cur.add_argument("action", choices=["eval"])
    p_cur.add_argument("--date")
    subparsers.add_parser("dashboard", help="Dashboard")
    subparsers.add_parser("repair", help="Repair")

    args = parser.parse_args()
    if args.command == "jules":
        if args.action == "done":
            args.task_id = args.content
        cmd_jules(args)
    elif args.command == "curator":
        cmd_curator(args)
    elif args.command == "process":
        cmd_process(args)
    elif args.command == "novel":
        cmd_novel(args)
    elif args.command == "sync":
        cmd_sync(args)
    elif args.command == "image-generate":
        cmd_image_generate(args)
    elif args.command == "transcribe":
        cmd_transcribe(args)
    elif args.command == "summarize":
        cmd_summarize(args)
    elif args.command == "pending":
        cmd_pending(args)
    elif args.command == "dashboard":
        cmd_dashboard(args)
    elif args.command == "repair":
        cmd_repair(args)


def cmd_curator(args):
    from src.use_cases.evaluate import EvaluateDailyContentUseCase

    EvaluateDailyContentUseCase().execute(args.date)


def cmd_dashboard(args):
    from src.infrastructure.dashboard import Dashboard

    Dashboard().render()


def cmd_repair(args):
    from src.infrastructure.agents.pipeline_repair import PipelineRepairAgent

    PipelineRepairAgent().run()


if __name__ == "__main__":
    main()
