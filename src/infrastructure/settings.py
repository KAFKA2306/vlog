import platform
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


from src.models import AppConfig, Prompts


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def load_config() -> AppConfig:
    path = _get_project_root() / "data/config.yaml"
    return AppConfig.model_validate(yaml.safe_load(path.read_text(encoding="utf-8"))) if path.exists() else AppConfig()


def load_prompts() -> Prompts:
    path = _get_project_root() / "data/prompts.yaml"
    return Prompts.model_validate(yaml.safe_load(path.read_text(encoding="utf-8"))) if path.exists() else Prompts()


_cfg = load_config()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    gemini_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    gemini_model: str = _cfg.gemini.model
    novel_model: str = _cfg.novel.model
    novel_max_output_tokens: int = _cfg.novel.max_output_tokens
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_service_role_key: str = Field(default="", alias="SUPABASE_SERVICE_ROLE_KEY")
    check_interval: int = _cfg.process.check_interval
    process_names: set[str] = Field(default_factory=lambda: set(_cfg.process.names.split(",")))
    recording_dir: Path = Path(_cfg.paths.recording_dir)
    sample_rate: int = _cfg.audio.sample_rate
    channels: int = _cfg.audio.channels
    block_size: int = _cfg.audio.block_size
    whisper_model_size: str = _cfg.whisper.model_size
    whisper_device: str = _cfg.whisper.device
    whisper_compute_type: str = _cfg.whisper.compute_type
    transcript_dir: Path = Path(_cfg.paths.transcript_dir)
    summary_dir: Path = Path(_cfg.paths.summary_dir)
    photo_prompt_dir: Path = Path(_cfg.paths.photo_prompt_dir)
    photo_dir: Path = Path(_cfg.paths.photo_dir)
    novel_out_dir: Path = Path(_cfg.novel.out_dir)
    image_model: str = _cfg.image.model
    image_device: str = _cfg.image.device
    image_height: int = _cfg.image.height
    image_width: int = _cfg.image.width
    archive_after_process: bool = _cfg.processing.archive_after_process
    record_only: bool = _cfg.processing.record_only
    archive_dir: Path = Path(_cfg.paths.archive_dir)
    trace_file: Path = Path(_cfg.paths.trace_file)
    prompts: Prompts = load_prompts()


settings = Settings()
