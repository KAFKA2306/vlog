from datetime import datetime

from pydantic import BaseModel, Field


class RecordingSession(BaseModel):
    start_time: datetime
    file_paths: tuple[str, ...]
    end_time: datetime | None = None


class ActivityTask(BaseModel):
    id: str
    created_at: datetime
    status: str = "pending"
    type: str | None = None
    file_paths: list[str] = Field(default_factory=list)
    novel_path: str | None = None
    photo_path: str | None = None
    start_time: str | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    retry_count: int = 0
