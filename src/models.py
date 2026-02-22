from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class RecordingSession(BaseModel):
    model_config = ConfigDict(frozen=True)
    start_time: datetime
    file_paths: tuple[str, ...]
    end_time: datetime | None = None


class ActivityTask(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    created_at: datetime
    status: str = "pending"
    type: str | None = None
    file_paths: Annotated[list[str], Field(default_factory=list)]
    novel_path: str | None = None
    photo_path: str | None = None
    start_time: str | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    retry_count: int = 0


class DailyEntry(BaseModel):
    model_config = ConfigDict(frozen=True)
    file_path: str
    date: date
    title: str
    content: str
    tags: tuple[str, ...] = ("summary",)
    is_public: bool = True
    image_url: str | None = None


class Evaluation(BaseModel):
    model_config = ConfigDict(frozen=True)
    date: date
    target_type: str = "novel"
    quality_score: float
    faithfulness_score: float
    reasoning: str


class GeminiConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    model: str = "models/gemini-2.5-flash"


class NovelConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    model: str = "models/gemini-2.5-flash"
    max_output_tokens: int = 8192
    out_dir: str = "data/novels"


class PathsConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    recording_dir: str = "data/recordings"
    transcript_dir: str = "data/transcripts"
    summary_dir: str = "data/summaries"
    photo_prompt_dir: str = "data/photos_prompts"
    photo_dir: str = "data/photos"
    archive_dir: str = "data/archives"
    trace_file: str = "data/traces.jsonl"


class WhisperConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    model_size: str = "large-v3"
    device: str = "cuda"
    compute_type: str = "float16"


class AudioConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    sample_rate: int = 16000
    channels: int = 1
    block_size: int = 1024


class ImageConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    model: str = "Tongyi-MAI/Z-Image-Turbo"
    device: str = "cuda"
    height: int = 1024
    width: int = 1024


class ProcessConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    check_interval: int = 5
    names: str = "VRChat"


class JuleConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    model: str = "models/gemini-2.5-flash"


class ProcessingConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    archive_after_process: bool = True
    record_only: bool = False


class AppConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    gemini: GeminiConfig = Field(default_factory=GeminiConfig)
    novel: NovelConfig = Field(default_factory=NovelConfig)
    jules: JuleConfig = Field(default_factory=JuleConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    whisper: WhisperConfig = Field(default_factory=WhisperConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    image: ImageConfig = Field(default_factory=ImageConfig)
    process: ProcessConfig = Field(default_factory=ProcessConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)


class Prompts(BaseModel):
    model_config = ConfigDict(frozen=True, extra="allow")
    summary: str = ""
    novel: str = ""
    photo: str = ""
