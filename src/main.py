import logging
import os
import sys
from pathlib import Path


def setup_logging():
    log_path = Path("data/logs/vlog.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path, mode="w", encoding="utf-8"),
        ],
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("faster_whisper").setLevel(logging.WARNING)
    print(f"Logging configured. Logs available at: {log_path.absolute()}")


if __name__ == "__main__":
    setup_logging()

    from src.app import Application

    args = set(sys.argv[1:])

    if "fill-photos" in args:
        from src.use_cases.fill_gaps import PhotoGapFillerUseCase

        print("Scanning for missing photos...")
        PhotoGapFillerUseCase().execute()
    else:
        record_only = "record-only" in args or os.environ.get("RECORD_ONLY", "").lower() in {
            "1",
            "true",
            "yes",
        }
        Application(record_only=record_only).run()
