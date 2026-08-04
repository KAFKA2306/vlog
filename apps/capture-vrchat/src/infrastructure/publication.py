from pathlib import Path

from src.domain.publication import has_publishable_source
from src.infrastructure.daily_state import DailyStateStore
from src.infrastructure.settings import settings


def is_publishable_summary(date_str: str) -> bool:
    entry = DailyStateStore().get(date_str)
    source_files = entry.get("summary_source_files", [])
    if not isinstance(source_files, list) or not source_files:
        return False

    paths = tuple(
        settings.transcript_dir / Path(str(name)).name for name in source_files
    )
    if not all(path.is_file() for path in paths):
        return False

    texts = tuple(path.read_text(encoding="utf-8") for path in paths)
    return has_publishable_source(texts, settings.min_transcript_size_bytes)
