from dataclasses import dataclass
from datetime import datetime


@dataclass
class RecordingSession:
    start_time: datetime
    file_path: str
    end_time: datetime | None = None


@dataclass
class DiaryEntry:
    date: datetime
    summary: str
    raw_log: str
    session_start: datetime
    session_end: datetime
    diary_path: str | None = None
    transcript_path: str | None = None
