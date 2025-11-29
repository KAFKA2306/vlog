import argparse

from src.infrastructure.file_repository import FileRepository
from src.infrastructure.preprocessor import TranscriptPreprocessor
from src.infrastructure.summarizer import Summarizer
from src.infrastructure.supabase_repository import SupabaseRepository
from src.infrastructure.transcriber import Transcriber
from src.use_cases.process_recording import ProcessRecordingUseCase


def cmd_process(args):
    use_case = ProcessRecordingUseCase(
        transcriber=Transcriber(),
        preprocessor=TranscriptPreprocessor(),
        summarizer=Summarizer(),
        storage=SupabaseRepository(),
        file_repository=FileRepository(),
    )
    use_case.execute(args.file)


def cmd_novel(args):
    from src.infrastructure.novelizer import Novelizer
    from src.use_cases.build_novel import BuildNovelUseCase

    use_case = BuildNovelUseCase(Novelizer())
    novel_path = use_case.execute(args.date)

    if novel_path:
        print(f"章を追加: {novel_path}")
        SupabaseRepository().sync()
    else:
        print("Novel Builder is disabled")


def cmd_sync(args):
    SupabaseRepository().sync()
    print("Synced with Supabase")


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

    args = parser.parse_args()

    if args.command == "process":
        cmd_process(args)
    elif args.command == "novel":
        cmd_novel(args)
    elif args.command == "sync":
        cmd_sync(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
