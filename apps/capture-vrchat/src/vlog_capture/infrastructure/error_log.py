from datetime import datetime, timedelta
from pathlib import Path

from vlog_capture.domain.error_events import ErrorEvent
from vlog_capture.infrastructure.settings import settings


class ErrorLogRepository:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or settings.error_log_file

    def append(self, event: ErrorEvent) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(event.model_dump_json() + "\n")

    def recent(self, days: int) -> list[ErrorEvent]:
        since = datetime.now() - timedelta(days=days)
        if not self._path.exists():
            return []
        with self._path.open("r", encoding="utf-8") as handle:
            return [
                event
                for line in handle
                if line.strip()
                if (event := ErrorEvent.model_validate_json(line)).timestamp >= since
            ]
