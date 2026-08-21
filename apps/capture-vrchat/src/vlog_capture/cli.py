import argparse
from collections.abc import Callable

from vlog_capture.cli_handlers import (
    cmd_curator,
    cmd_daily,
    cmd_error,
    cmd_image_generate,
    cmd_jules,
    cmd_manga,
    cmd_pending,
    cmd_process,
    cmd_record,
    cmd_summarize,
    cmd_transcribe,
)
from vlog_capture.secure_handlers import cmd_audit, cmd_notify, cmd_novel, cmd_sync

Handler = Callable[[argparse.Namespace], None]


def _command(
    subparsers: argparse._SubParsersAction,
    name: str,
    help_text: str,
    handler: Handler,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(name, help=help_text)
    parser.set_defaults(handler=handler)
    return parser


def main() -> None:
    parser = argparse.ArgumentParser(description="VLog CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_process = _command(subparsers, "process", "Process audio file", cmd_process)
    p_process.add_argument("--file", required=True, help="Path to audio file")
    p_process.add_argument("--sync", action="store_true", default=True)
    p_process.add_argument("--no-sync", dest="sync", action="store_false")

    _command(subparsers, "record", "Record audio until interrupted", cmd_record)

    p_novel = _command(subparsers, "novel", "Generate novel chapter", cmd_novel)
    p_novel.add_argument("--date", help="Target date (YYYYMMDD); defaults to today")
    p_novel.add_argument("--out", help="Output filename")

    _command(subparsers, "sync", "Strictly sync data to Supabase", cmd_sync)

    p_image_generate = _command(
        subparsers, "image-generate", "Generate image", cmd_image_generate
    )
    p_image_generate.add_argument("--novel-file", required=True)
    p_image_generate.add_argument("--output-file")

    p_manga = _command(subparsers, "manga", "Generate 4-koma manga", cmd_manga)
    p_manga.add_argument("--novel-file", required=True)

    p_transcribe = _command(
        subparsers, "transcribe", "Transcribe audio file", cmd_transcribe
    )
    p_transcribe.add_argument("--file", required=True)

    p_summarize = _command(
        subparsers, "summarize", "Summarize transcript", cmd_summarize
    )
    p_summarize.add_argument("--file")
    p_summarize.add_argument("--date")

    _command(subparsers, "daily", "Run daily pipeline", cmd_daily)
    _command(subparsers, "pending", "Process pending and verify sync", cmd_pending)

    p_jules = _command(subparsers, "jules", "Manage tasks", cmd_jules)
    p_jules.add_argument("action", choices=["add", "list", "done"])
    p_jules.add_argument("content", nargs="?")

    p_curator = _command(subparsers, "curator", "Evaluate", cmd_curator)
    p_curator.add_argument("action", choices=["eval"])
    p_curator.add_argument("--date")

    p_notify = _command(subparsers, "notify", "Notify Discord", cmd_notify)
    p_notify.add_argument("--message", required=True)

    p_audit = _command(subparsers, "audit", "Audit one correlated run", cmd_audit)
    p_audit.add_argument("--run-id")
    p_audit.add_argument("--json", action="store_true")
    p_audit.add_argument("--strict", action="store_true", default=True)
    p_audit.add_argument("--no-strict", dest="strict", action="store_false")
    p_audit.add_argument("--recent", type=int, default=100)
    p_audit.add_argument("--trace-window-minutes", type=int, default=30)

    p_error = _command(subparsers, "error", "Manage structured error logs", cmd_error)
    p_error.add_argument("action", choices=["report", "record"])
    p_error.add_argument("--days", type=int, default=30)
    p_error.add_argument("--stage")
    p_error.add_argument("--kind")
    p_error.add_argument("--reason")
    p_error.add_argument("--task-name", default="manual")
    p_error.add_argument("--recording-path")

    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
