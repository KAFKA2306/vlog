import argparse

from src.use_cases.process_recording import ProcessRecordingUseCase


def cmd_process(args):
    use_case = ProcessRecordingUseCase()
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
