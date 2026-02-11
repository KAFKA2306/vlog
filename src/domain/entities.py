from dataclasses import dataclass
from datetime import datetime
@dataclass
class RecordingSession:
    start_time: datetime
    file_paths: tuple[str, ...]
    end_time: datetime | None = None
