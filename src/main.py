import logging
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

    if len(sys.argv) > 1 and sys.argv[1] == "fill-photos":
        from src.use_cases.fill_gaps import PhotoGapFillerUseCase

        print("Scanning for missing photos...")
        PhotoGapFillerUseCase().execute()
    else:
        Application().run()
