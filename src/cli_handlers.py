import argparse
import re
from pathlib import Path

from src.infrastructure.ai import ImageGenerator, JulesClient, Novelizer, Summarizer
from src.infrastructure.repositories import (
    FileRepository,
    SupabaseRepository,
    TaskRepository,
)
from src.infrastructure.system import Transcriber, TranscriptPreprocessor
from src.use_cases.build_novel import BuildNovelUseCase
from src.use_cases.process_recording import ProcessRecordingUseCase


def cmd_process(args: argparse.Namespace) -> None:
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
    use_case = BuildNovelUseCase(Novelizer(), ImageGenerator())
    use_case.execute(args.date)
    SupabaseRepository().sync()


def cmd_sync(args: argparse.Namespace) -> None:
    SupabaseRepository().sync()


def cmd_image_generate(args: argparse.Namespace) -> None:
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
    repo = TaskRepository()
    if args.action == "add":
        task_data = JulesClient().parse_task(args.content)
        repo.add(task_data)
    elif args.action == "list":
        repo.list_pending()
    elif args.action == "done":
        repo.complete(args.task_id)


def cmd_transcribe(args: argparse.Namespace) -> None:
    Transcriber().transcribe_and_save(args.file)


def cmd_summarize(args: argparse.Namespace) -> None:
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
    use_case = BuildNovelUseCase(Novelizer(), ImageGenerator())
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

    EvaluateDailyContentUseCase().execute(args.date)


def cmd_notify(args: argparse.Namespace) -> None:
    from src.infrastructure.discord import DiscordClient

    DiscordClient().send_message(args.message)
