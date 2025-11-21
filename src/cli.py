import argparse
import time
from datetime import datetime

from src.domain.entities import DiaryEntry, RecordingSession
from src.infrastructure.audio_recorder import AudioRecorder
from src.infrastructure.diary_writer import DiaryWriter
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
    session = RecordingSession(
        file_path="dummy", start_time=datetime.now(), end_time=datetime.now()
    )
    summarizer = Summarizer()
    print("Summarizing...")
    summary = summarizer.summarize(text, session)
    print("--- Summary ---")
    print(summary)


def cmd_write(args):
    with open(args.file, "r", encoding="utf-8") as f:
        text = f.read()
    now = datetime.now()
    entry = DiaryEntry(
        date=now,
        summary=text,
        raw_log="",
        session_start=now,
        session_end=now,
    )
    writer = DiaryWriter()
    path = writer.write(entry)
    print(f"Diary entry written to: {path}")


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
    summarizer = Summarizer()
    print("Summarizing...")
    summary = summarizer.summarize(transcript, session)
    entry = DiaryEntry(
        date=start_time,
        summary=summary,
        raw_log=transcript,
        session_start=start_time,
        session_end=datetime.now(),
    )
    writer = DiaryWriter()
    path = writer.write(entry)
    print(f"Processing complete. Diary entry written to: {path}")


def main():
    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser(description="VLog CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Check
    subparsers.add_parser("check", help="Check if VRChat is running")

    # Record
    subparsers.add_parser("record", help="Record audio manually")

    # Transcribe
    p_transcribe = subparsers.add_parser("transcribe", help="Transcribe audio file")
    p_transcribe.add_argument("--file", help="Path to audio file")

    # Summarize
    p_summarize = subparsers.add_parser("summarize", help="Summarize text file")
    p_summarize.add_argument("--file", help="Path to text file")

    # Write
    p_write = subparsers.add_parser("write", help="Write diary entry from text file")
    p_write.add_argument("--file", help="Path to text file containing summary")

    # Process
    p_process = subparsers.add_parser(
        "process", help="Process audio file (Transcribe -> Summarize -> Write)"
    )
    p_process.add_argument("--file", help="Path to audio file")

    args = parser.parse_args()

    commands = {
        "check": cmd_check,
        "record": cmd_record,
        "transcribe": cmd_transcribe,
        "summarize": cmd_summarize,
        "write": cmd_write,
        "process": cmd_process,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
