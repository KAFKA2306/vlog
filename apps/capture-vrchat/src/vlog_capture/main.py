import logging
import sys

from vlog_capture.app import Application
from vlog_capture.portability import runtime_directories


def setup_logging() -> None:
    log_dir = runtime_directories().state / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "vlog.log", encoding="utf-8"),
        ],
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("faster_whisper").setLevel(logging.WARNING)


def main() -> None:
    setup_logging()
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
