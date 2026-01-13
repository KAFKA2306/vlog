import argparse

from src.infrastructure.ai import (
    ImageGenerator,
    JulesClient,
    Novelizer,
    Summarizer,
)
from src.infrastructure.repositories import (
    FileRepository,
    SupabaseRepository,
)
from src.infrastructure.system import Transcriber, TranscriptPreprocessor
from src.use_cases.build_novel import BuildNovelUseCase
from src.use_cases.process_recording import ProcessRecordingUseCase


def cmd_process(args):
    use_case = ProcessRecordingUseCase(
        transcriber=Transcriber(),
        preprocessor=TranscriptPreprocessor(),
        summarizer=Summarizer(),
        storage=SupabaseRepository(),
        file_repository=FileRepository(),
        novelizer=Novelizer(),
        image_generator=ImageGenerator(),
    )
    use_case.execute(args.file)


def cmd_novel(args):
    use_case = BuildNovelUseCase(Novelizer(), ImageGenerator())
    novel_path = use_case.execute(args.date)

    if novel_path:
        print(f"章を追加: {novel_path}")
        SupabaseRepository().sync()
    else:
        print("要約ファイルが見つかりません")


def cmd_sync(args):
    SupabaseRepository().sync()
    print("Synced with Supabase")


def cmd_image_generate(args):
    from pathlib import Path

    novel_path = Path(args.novel_file)
    if not novel_path.exists():
        print(f"Error: Novel file not found at {novel_path}")
        return

    novel_content = novel_path.read_text(encoding="utf-8")

    output_path = (
        Path(args.output_file)
        if args.output_file
        else novel_path.parent / (novel_path.stem + ".png")
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating image for {novel_path} to {output_path}...")
    image_generator = ImageGenerator()
    image_generator.generate_from_novel(novel_content, output_path)
    print(f"Image generated successfully to {output_path}")


def cmd_jules(args):
    from src.infrastructure.repositories import TaskRepository

    repo = TaskRepository()

    if args.action == "add":
        if not args.content:
            print("Error: content is required for 'add'")
            return

        print(f"Jules is thinking about: {args.content}...")
        client = JulesClient()
        task_data = client.parse_task(args.content)

        new_task = repo.add(task_data)
        print(
            f"Task added: [{new_task['priority'].upper()}] {new_task['title']} "
            f"(ID: {new_task['id'][:8]})"
        )

    elif args.action == "list":
        tasks = repo.list_pending()
        if not tasks:
            print("No pending tasks.")
            return
        print(f"Found {len(tasks)} pending tasks:")
        for t in tasks:
            print(f"- [{t['id'][:8]}] {t['title']} ({t.get('priority', 'normal')})")

    elif args.action == "done":
        if not args.task_id:
            print("Error: task_id is required for 'done'")
            return
        completed = repo.complete(args.task_id)
        if completed:
            print(f"Completed: {completed['title']}")
        else:
            print("Task not found.")


def cmd_transcribe(args):
    transcriber = Transcriber()
    transcriber.transcribe_and_save(args.file)
    print(f"Transcribed: {args.file}")


def cmd_summarize(args):
    import re
    from pathlib import Path

    file_repo = FileRepository()
    summarizer = Summarizer()

    if getattr(args, "date", None):
        date_str = args.date
        transcript_dir = Path("data/transcripts")
        files = sorted(list(transcript_dir.glob(f"cleaned_{date_str}_*.txt")))
        if not files:
            files = sorted(list(transcript_dir.glob(f"{date_str}_*.txt")))

        if not files:
            print(f"No transcripts found for date: {date_str}")
            return

        print(f"Summarizing {len(files)} transcripts for {date_str}...")
        combined_text = ""
        for f in files:
            text = file_repo.read(str(f))
            combined_text += f"\n\n--- {f.name} ---\n{text}"

        summary = summarizer.summarize(combined_text, date_str=date_str)
        file_repo.save_summary(summary, date_str)
        print(f"Summarized date {date_str} to data/summaries/{date_str}_summary.txt")

    elif args.file:
        input_path = Path(args.file)
        if input_path.suffix in [".txt", ".md"]:
            transcript_text = file_repo.read(args.file)
            transcript_path = input_path
        else:
            transcript_path = Path("data/transcripts") / f"{input_path.stem}.txt"
            if not transcript_path.exists():
                print(f"Transcript not found: {transcript_path}")
                return
            transcript_text = file_repo.read(str(transcript_path))

        stem = input_path.stem
        match = re.search(r"(\d{8})", stem)
        date_str = match.group(1) if match else stem.split("_")[0]

        summary = summarizer.summarize(transcript_text, date_str=date_str)
        file_repo.save_summary(summary, date_str)
        print(f"Summarized: {args.file}")
    else:
        print("Error: Either --file or --date must be specified")


def cmd_pending(args):
    import re
    from pathlib import Path

    transcript_dir = Path("data/transcripts")
    summary_dir = Path("data/summaries")
    novel_dir = Path("data/novels")
    recording_dir = Path("data/recordings")

    pending_transcription = []

    for f in recording_dir.glob("*"):
        if f.suffix.lower() not in [".wav", ".flac", ".mp3"]:
            continue

        transcript_path = transcript_dir / f"{f.stem}.txt"
        if not transcript_path.exists():
            pending_transcription.append(f)

    print(f"Missing transcripts: {len(pending_transcription)}")

    file_repo = FileRepository()

    if pending_transcription:
        transcriber = Transcriber()
        preprocessor = TranscriptPreprocessor()

        for audio_path in pending_transcription:
            print(f"Transcribing {audio_path.name}...")
            transcript, saved_path = transcriber.transcribe_and_save(str(audio_path))

            cleaned = preprocessor.process(transcript)
            cleaned_path = str(
                Path(saved_path).with_name(f"cleaned_{Path(saved_path).name}")
            )
            file_repo.save_text(cleaned_path, cleaned)
            print(f"  Created {Path(saved_path).name} and cleaned version")

        transcriber.unload()

    dates = set()
    for f in transcript_dir.glob("*.txt"):
        match = re.search(r"(\d{8})", f.stem)
        if match:
            dates.add(match.group(1))

    dates = sorted(dates)
    print(f"Found {len(dates)} unique dates with transcripts")

    pending_summary = []
    pending_novel = []

    for date_str in dates:
        summary_path = summary_dir / f"{date_str}_summary.txt"
        novel_path = novel_dir / f"{date_str}.md"

        if not summary_path.exists():
            pending_summary.append(date_str)
        if not novel_path.exists():
            pending_novel.append(date_str)

    print(f"Missing summaries: {len(pending_summary)}")
    print(f"Missing novels: {len(pending_novel)}")

    summarizer = Summarizer()

    for date_str in pending_summary:
        print(f"Generating summary for {date_str}...")
        files = sorted(list(transcript_dir.glob(f"cleaned_{date_str}_*.txt")))
        if not files:
            files = sorted(list(transcript_dir.glob(f"{date_str}_*.txt")))

        if not files:
            print("  No transcripts found, skipping")
            continue

        combined_text = ""
        for f in files:
            text = file_repo.read(str(f))
            combined_text += f"\n\n--- {f.name} ---\n{text}"

        summary = summarizer.summarize(combined_text, date_str=date_str)
        file_repo.save_summary(summary, date_str)
        print(f"  Created {date_str}_summary.txt")

    use_case = BuildNovelUseCase(Novelizer(), ImageGenerator())
    for date_str in pending_novel:
        summary_path = summary_dir / f"{date_str}_summary.txt"
        if not summary_path.exists():
            print(f"Skipping novel for {date_str} (no summary)")
            continue

        print(f"Generating novel for {date_str}...")
        novel_path = use_case.execute(date_str)
        if novel_path:
            print(f"  Created {novel_path.name}")

    if pending_transcription or pending_summary or pending_novel:
        print("Syncing to Supabase...")
        SupabaseRepository().sync()
        print("Done!")
    else:
        print("All data is up to date!")


def main():
    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser(description="VLog CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    p_process = subparsers.add_parser("process", help="Process audio file")
    p_process.add_argument("--file", help="Path to audio file")

    p_novel = subparsers.add_parser("novel", help="Generate novel chapter")
    p_novel.add_argument("--date", help="Target date (YYYYMMDD)")
    p_novel.add_argument("--out", help="Output filename (unused)")

    subparsers.add_parser("sync", help="Sync data to Supabase")

    p_image_generate = subparsers.add_parser(
        "image-generate", help="Generate an image from a novel file"
    )
    p_image_generate.add_argument(
        "--novel-file", required=True, help="Path to the novel markdown file"
    )
    p_image_generate.add_argument(
        "--output-file", help="Path to the output image file (optional)"
    )

    p_transcribe = subparsers.add_parser("transcribe", help="Transcribe audio file")
    p_transcribe.add_argument("--file", required=True, help="Path to audio file")

    p_summarize = subparsers.add_parser("summarize", help="Summarize transcript")
    p_summarize.add_argument("--file", help="Path to audio/text file")
    p_summarize.add_argument(
        "--date", help="Target date (YYYYMMDD) to merge and summarize"
    )

    subparsers.add_parser(
        "pending", help="Process all pending (missing) summaries and novels"
    )

    p_jules = subparsers.add_parser("jules", help="Manage mini-tasks with Jules AI")
    p_jules.add_argument(
        "action", choices=["add", "list", "done"], help="Action to perform"
    )
    p_jules.add_argument(
        "content", nargs="?", help="Task content (for add) or Task ID (for done)"
    )

    args = parser.parse_args()
    if args.command == "jules":
        if args.action == "done":
            args.task_id = args.content
        cmd_jules(args)
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
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
