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


def main():
    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser(description="VLog CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    p_process = subparsers.add_parser("process", help="Process audio file")
    p_process.add_argument("--file", help="Path to audio file")

    args = parser.parse_args()

    if args.command == "process":
        cmd_process(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
