from dataclasses import dataclass
from datetime import datetime

@dataclass
class RecordingSession:
    start_time: datetime
    file_path: str

@dataclass
class DiaryEntry:
    date: datetime
    summary: str
    raw_log: str
