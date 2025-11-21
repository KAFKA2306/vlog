import argparse
import time
from datetime import datetime
from pathlib import Path

from src.domain.entities import RecordingSession
from src.infrastructure.audio_recorder import AudioRecorder
from src.infrastructure.preprocessor import TranscriptPreprocessor
from src.infrastructure.process_monitor import ProcessMonitor
from src.infrastructure.summarizer import Summarizer
from src.infrastructure.transcriber import Transcriber


def cmd_check(args):
    monitor = ProcessMonitor()
    if monitor.is_running():
        print("VRChat is running.")
    else:
        print("VRChat is NOT running.")


def cmd_record(args):
    recorder = AudioRecorder()
    print("Recording... Press Ctrl+C to stop.")
    recorder.start()
    while True:
        time.sleep(0.1)


def cmd_transcribe(args):
    transcriber = Transcriber()
    print(f"Transcribing {args.file}...")
    text = transcriber.transcribe(args.file)
    transcriber.unload()
    print("--- Transcript ---")
    print(text)


def cmd_summarize(args):
    with open(args.file, "r", encoding="utf-8") as f:
        text = f.read()

    print("Preprocessing transcript...")
    preprocessor = TranscriptPreprocessor()
    cleaned_text = preprocessor.process(text)

    session = RecordingSession(
        file_path="dummy", start_time=datetime.now(), end_time=datetime.now()
    )
    summarizer = Summarizer()
    print("Summarizing...")
    summary = summarizer.summarize(cleaned_text, session)
    print("--- Summary ---")
    print(summary)

    output_path = Path("summaries") / f"{Path(args.file).stem}_summary.txt"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(summary, encoding="utf-8")
    print(f"\nSummary saved to: {output_path}")


def cmd_process(args):
    transcriber = Transcriber()
    print(f"Transcribing {args.file}...")
    transcript = transcriber.transcribe(args.file)
    transcriber.unload()
    try:
        basename = args.file.split("/")[-1].split(".")[0]
        start_time = datetime.strptime(basename, "%Y%m%d_%H%M%S")
    except ValueError:
        start_time = datetime.now()
    session = RecordingSession(
        file_path=args.file,
        start_time=start_time,
        end_time=datetime.now(),
    )

    print("Preprocessing transcript...")
    preprocessor = TranscriptPreprocessor()
    cleaned_transcript = preprocessor.process(transcript)

    summarizer = Summarizer()
    print("Summarizing...")
    summary = summarizer.summarize(cleaned_transcript, session)

    output_path = Path("summaries") / f"{Path(args.file).stem}_summary.txt"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(summary, encoding="utf-8")
    print(f"Processing complete. Summary saved to: {output_path}")


def main():
    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser(description="VLog CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("check", help="Check if VRChat is running")
    subparsers.add_parser("record", help="Record audio manually")
    p_transcribe = subparsers.add_parser("transcribe", help="Transcribe audio file")
    p_transcribe.add_argument("--file", help="Path to audio file")
    p_summarize = subparsers.add_parser("summarize", help="Summarize text file")
    p_summarize.add_argument("--file", help="Path to text file")
    p_process = subparsers.add_parser(
        "process", help="Process audio file (Transcribe -> Summarize)"
    )
    p_process.add_argument("--file", help="Path to audio file")

    args = parser.parse_args()

    commands = {
        "check": cmd_check,
        "record": cmd_record,
        "transcribe": cmd_transcribe,
        "summarize": cmd_summarize,
        "process": cmd_process,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
