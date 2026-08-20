from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Any, Dict, List, Set

import yaml
from pydantic import AliasChoices, Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from vlog_capture.portability import (
    PathFlavor,
    classify_path,
    runtime_directories,
)
from vlog_capture.project import PROJECT_ROOT


def _get_project_root() -> Path:
    """Return the immutable code/config checkout root."""

    return PROJECT_ROOT


def is_windows_path_invalid_on_linux(value: Path, *, system: str | None = None) -> bool:
    runtime_system = system or platform.system()
    return runtime_system == "Linux" and classify_path(str(value)) in {
        PathFlavor.WINDOWS_ABSOLUTE,
        PathFlavor.WINDOWS_UNC,
    }


def is_posix_path_invalid_on_windows(value: Path, *, system: str | None = None) -> bool:
    runtime_system = system or platform.system()
    return (
        runtime_system == "Windows"
        and classify_path(str(value)) == PathFlavor.POSIX_ABSOLUTE
    )


def _validate_host_path(value: Path) -> Path:
    if is_windows_path_invalid_on_linux(value):
        raise ValueError(f"Windows path is not valid in WSL: {value}")
    if is_posix_path_invalid_on_windows(value):
        raise ValueError(f"POSIX absolute path is not valid on Windows: {value}")
    return value


def resolve_project_path(value: Path) -> Path:
    """Resolve read-only repository assets such as bundled config/prompts."""

    value = _validate_host_path(value)
    if value.is_absolute():
        return value
    return _get_project_root() / value


def resolve_runtime_path(value: Path, kind: str) -> Path:
    """Resolve mutable runtime paths outside the Git checkout by default."""

    value = _validate_host_path(value)
    if value.is_absolute():
        return value
    directories = runtime_directories()
    base = {
        "config": directories.config,
        "data": directories.data,
        "state": directories.state,
        "cache": directories.cache,
    }[kind]
    return base / value


def _runtime_default(kind: str, *parts: str) -> Path:
    directories = runtime_directories()
    return getattr(directories, kind).joinpath(*parts)


def _normalize_legacy_environment() -> None:
    """Map legacy process variable names to the canonical VLOG_* namespace once.

    This is a name-compatibility bridge, not another configuration parser. Process
    environment still outranks VLOG_ENV_FILE, and an explicitly supplied canonical
    variable always wins over its legacy spelling.
    """

    aliases = {
        "GOOGLE_API_KEY": "VLOG_GEMINI_API_KEY",
        "GOOGLE_JULES_API_KEY": "VLOG_JULES_API_KEY",
        "SUPABASE_URL": "VLOG_SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY": "VLOG_SUPABASE_SERVICE_ROLE_KEY",
        "DISCORD_WEBHOOK_URL": "VLOG_DISCORD_WEBHOOK_URL",
        "VLOG_ERROR_EVENT_FILE": "VLOG_ERROR_LOG_FILE",
    }
    for legacy, canonical in aliases.items():
        if canonical not in os.environ and legacy in os.environ:
            os.environ[canonical] = os.environ[legacy]


def _settings_env_file() -> Path | None:
    """Return the one explicitly authorized dotenv file, if configured."""

    raw = os.environ.get("VLOG_ENV_FILE")
    if not raw:
        return None
    path = _validate_host_path(Path(raw).expanduser())
    if not path.is_absolute():
        raise RuntimeError("VLOG_ENV_FILE must be an absolute path")
    return path


def load_config() -> Dict[str, Any]:
    """Load versioned, non-secret application defaults from the repository."""

    config_path = _get_project_root() / "data/config.yaml"
    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    return {}


def load_prompts() -> Dict[str, Any]:
    """Load versioned prompt templates from the repository."""

    prompts_path = _get_project_root() / "data/prompts.yaml"
    if prompts_path.exists():
        with prompts_path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    return {}


_config = load_config()
_prompts = load_prompts()

_DEFAULT_LLM_MODEL = _config.get("gemini", {}).get(
    "model", "gemini-3.1-flash-lite-preview"
)


class Settings(BaseSettings):
    """Canonical runtime configuration.

    Precedence is: explicit constructor values > process environment > the one
    optional VLOG_ENV_FILE passed at instantiation > versioned repository defaults.
    Mutable filesystem paths use VLOG_* overrides and otherwise live in the OS
    standard VLog config/data/state/cache homes.
    """

    model_config = SettingsConfigDict(
        extra="ignore",
        populate_by_name=True,
        case_sensitive=False,
    )

    gemini_api_key: str = Field(
        validation_alias=AliasChoices("VLOG_GEMINI_API_KEY", "GOOGLE_API_KEY")
    )
    gemini_model: str = _config.get("gemini", {}).get("model", _DEFAULT_LLM_MODEL)
    novel_model: str = _config.get("novel", {}).get("model", _DEFAULT_LLM_MODEL)
    novel_max_output_tokens: int = _config.get("novel", {}).get(
        "max_output_tokens", 8192
    )

    jules_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("VLOG_JULES_API_KEY", "GOOGLE_JULES_API_KEY"),
    )
    jules_model: str = _config.get("jules", {}).get("model", _DEFAULT_LLM_MODEL)

    supabase_url: str = Field(
        default="",
        validation_alias=AliasChoices("VLOG_SUPABASE_URL", "SUPABASE_URL"),
    )
    supabase_service_role_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "VLOG_SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SERVICE_ROLE_KEY"
        ),
    )
    discord_webhook_url: str = Field(
        default="",
        validation_alias=AliasChoices(
            "VLOG_DISCORD_WEBHOOK_URL", "DISCORD_WEBHOOK_URL"
        ),
    )

    check_interval: int = _config.get("process", {}).get("check_interval", 5)
    process_names: Set[str] = Field(
        default_factory=lambda: set(
            _config.get("process", {}).get("names", "VRChat").split(",")
        )
    )

    recording_dir: Path = Field(
        default_factory=lambda: _runtime_default("data", "recordings"),
        validation_alias="VLOG_RECORDING_DIR",
    )
    sample_rate: int = _config.get("audio", {}).get("sample_rate", 16000)
    channels: int = _config.get("audio", {}).get("channels", 1)
    block_size: int = _config.get("audio", {}).get("block_size", 1024)

    whisper_model_size: str = _config.get("whisper", {}).get("model_size", "large-v3")
    whisper_device: str = _config.get("whisper", {}).get("device", "cuda")
    whisper_compute_type: str = _config.get("whisper", {}).get(
        "compute_type", "float16"
    )
    transcript_dir: Path = Field(
        default_factory=lambda: _runtime_default("data", "transcripts"),
        validation_alias="VLOG_TRANSCRIPT_DIR",
    )
    summary_dir: Path = Field(
        default_factory=lambda: _runtime_default("data", "summaries"),
        validation_alias="VLOG_SUMMARY_DIR",
    )
    photo_prompt_dir: Path = Field(
        default_factory=lambda: _runtime_default("data", "photo_prompts"),
        validation_alias="VLOG_PHOTO_PROMPT_DIR",
    )
    photo_dir: Path = Field(
        default_factory=lambda: _runtime_default("data", "photos"),
        validation_alias="VLOG_PHOTO_DIR",
    )
    novel_out_dir: Path = Field(
        default_factory=lambda: _runtime_default("data", "novels"),
        validation_alias="VLOG_NOVEL_OUT_DIR",
    )

    manga_model: str = _config.get("manga", {}).get("model", _DEFAULT_LLM_MODEL)
    manga_out_dir: Path = Field(
        default_factory=lambda: _runtime_default("data", "manga"),
        validation_alias="VLOG_MANGA_OUT_DIR",
    )

    image_model: str = _config.get("image", {}).get("model", "Tongyi-MAI/Z-Image-Turbo")
    image_device: str = _config.get("image", {}).get("device", "cuda")
    image_height: int = _config.get("image", {}).get("height", 1024)
    image_width: int = _config.get("image", {}).get("width", 1024)
    image_num_inference_steps: int = _config.get("image", {}).get(
        "num_inference_steps", 9
    )
    image_guidance_scale: float = _config.get("image", {}).get("guidance_scale", 0.0)
    image_seed: int = _config.get("image", {}).get("seed", 42)
    image_prompt_filters: List[str] = _config.get("image", {}).get("prompt_filters", [])

    image_generator_default_prompt: str = (
        "(masterpiece, best quality:1.2), anime scenery, "
        "highly detailed, expressive lighting, aesthetic, {text}"
    )
    image_generator_default_negative_prompt: str = (
        "low quality, worst quality, bad anatomy, vr, headset, "
        "holding controller, holding object, holding weapon, "
        "floating objects, weird objects"
    )

    archive_after_process: bool = _config.get("processing", {}).get(
        "archive_after_process", True
    )
    min_transcript_size_bytes: int = _config.get("processing", {}).get(
        "min_transcript_size_bytes", 50
    )
    archive_dir: Path = Field(
        default_factory=lambda: _runtime_default("data", "archives"),
        validation_alias="VLOG_ARCHIVE_DIR",
    )
    trace_file: Path = Field(
        default_factory=lambda: _runtime_default("state", "traces.jsonl"),
        validation_alias="VLOG_TRACE_FILE",
    )
    profile_path: Path = Field(
        default_factory=lambda: _runtime_default("config", "profile.yaml"),
        validation_alias="VLOG_PROFILE_PATH",
    )
    incident_file: Path = Field(
        default_factory=lambda: _runtime_default("state", "incidents.jsonl"),
        validation_alias="VLOG_INCIDENT_FILE",
    )
    error_log_file: Path = Field(
        default_factory=lambda: _runtime_default("state", "error_events.jsonl"),
        validation_alias=AliasChoices("VLOG_ERROR_LOG_FILE", "VLOG_ERROR_EVENT_FILE"),
    )

    prompts: Dict[str, Any] = _prompts

    @field_validator(
        "recording_dir",
        "transcript_dir",
        "summary_dir",
        "novel_out_dir",
        "manga_out_dir",
        "photo_prompt_dir",
        "photo_dir",
        "archive_dir",
        mode="after",
    )
    @classmethod
    def normalize_data_path(cls, value: Path) -> Path:
        return resolve_runtime_path(value, "data")

    @field_validator("trace_file", "incident_file", "error_log_file", mode="after")
    @classmethod
    def normalize_state_path(cls, value: Path) -> Path:
        return resolve_runtime_path(value, "state")

    @field_validator("profile_path", mode="after")
    @classmethod
    def normalize_config_path(cls, value: Path) -> Path:
        return resolve_runtime_path(value, "config")

    @field_validator("process_names", mode="after")
    @classmethod
    def normalize_process_names(cls, value: Set[str], info: ValidationInfo) -> Set[str]:
        del info
        return {name.strip() for name in value if name.strip()}


_normalize_legacy_environment()
settings = Settings(
    _env_file=_settings_env_file(),
    _env_file_encoding="utf-8",
)
