import argparse

from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="VLog CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subparsers for commands (simplified)
    # Full command implementation moved to src/cli_handlers.py for simplicity & brevity
    from src.cli_handlers import (
        cmd_audit,
        cmd_check_vrc,
        cmd_curator,
        cmd_daily,
        cmd_image_generate,
        cmd_jules,
        cmd_manga,
        cmd_notify,
        cmd_novel,
        cmd_pending,
        cmd_process,
        cmd_summarize,
        cmd_sync,
        cmd_transcribe,
    )

    p_process = subparsers.add_parser("process", help="Process audio file")
    p_process.add_argument("--file", help="Path to audio file")
    p_process.add_argument("--sync", action="store_true", default=True)
    p_process.add_argument("--no-sync", dest="sync", action="store_false")

    p_novel = subparsers.add_parser("novel", help="Generate novel chapter")
    p_novel.add_argument("--date", help="Target date (YYYYMMDD)")
    p_novel.add_argument("--out", help="Output filename")

    subparsers.add_parser("sync", help="Sync data to Supabase")

    p_image_generate = subparsers.add_parser("image-generate", help="Generate image")
    p_image_generate.add_argument("--novel-file", required=True)
    p_image_generate.add_argument("--output-file")

    p_manga = subparsers.add_parser("manga", help="Generate 4-koma manga")
    p_manga.add_argument("--novel-file", required=True)

    p_transcribe = subparsers.add_parser("transcribe", help="Transcribe audio file")
    p_transcribe.add_argument("--file", required=True)

    p_summarize = subparsers.add_parser("summarize", help="Summarize transcript")
    p_summarize.add_argument("--file")
    p_summarize.add_argument("--date")

    subparsers.add_parser("daily", help="Run daily pipeline")
    subparsers.add_parser("pending", help="Process pending")

    p_jules = subparsers.add_parser("jules", help="Manage tasks")
    p_jules.add_argument("action", choices=["add", "list", "done"])
    p_jules.add_argument("content", nargs="?")

    p_curator = subparsers.add_parser("curator", help="Evaluate")
    p_curator.add_argument("action", choices=["eval"])
    p_curator.add_argument("--date")

    p_notify = subparsers.add_parser("notify", help="Notify Discord")
    p_notify.add_argument("--message", required=True)

    subparsers.add_parser("check-vrc", help="Check if VRChat is running")

    p_audit = subparsers.add_parser("audit", help="Run strict evidence-based audit")
    p_audit.add_argument("--recent", type=int, default=100)
    p_audit.add_argument("--trace-window-minutes", type=int, default=30)
    p_audit.add_argument("--json", action="store_true")
    p_audit.add_argument("--strict", action="store_true", default=True)
    p_audit.add_argument("--no-strict", dest="strict", action="store_false")

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
    elif args.command == "manga":
        cmd_manga(args)
    elif args.command == "transcribe":
        cmd_transcribe(args)
    elif args.command == "summarize":
        cmd_summarize(args)
    elif args.command == "daily":
        cmd_daily(args)
    elif args.command == "pending":
        cmd_pending(args)
    elif args.command == "notify":
        cmd_notify(args)
    elif args.command == "check-vrc":
        cmd_check_vrc(args)
    elif args.command == "audit":
        cmd_audit(args)


if __name__ == "__main__":
    main()
