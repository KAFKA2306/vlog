import platform
from pathlib import Path
from typing import Any, Dict, List, Set

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def load_config() -> Dict[str, Any]:
    config_path = _get_project_root() / "data/config.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def load_prompts() -> Dict[str, Any]:
    prompts_path = _get_project_root() / "data/prompts.yaml"
    if prompts_path.exists():
        with open(prompts_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


_config = load_config()
_prompts = load_prompts()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
    gemini_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    gemini_model: str = _config.get("gemini", {}).get(
        "model", "models/gemini-3-flash-preview"
    )
    novel_model: str = _config.get("novel", {}).get(
        "model", "models/gemini-3-flash-preview"
    )
    novel_max_output_tokens: int = _config.get("novel", {}).get(
        "max_output_tokens", 8192
    )
    jules_api_key: str = Field(default="", alias="GOOGLE_JULES_API_KEY")
    jules_model: str = _config.get("jules", {}).get(
        "model", "models/gemini-3-flash-preview"
    )
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_service_role_key: str = Field(
        default="", alias="SUPABASE_SERVICE_ROLE_KEY"
    )
    check_interval: int = _config.get("process", {}).get("check_interval", 5)
    process_names: Set[str] = Field(
        default_factory=lambda: set(
            _config.get("process", {}).get("names", "VRChat").split(",")
        )
    )
    recording_dir: Path = Field(
        default_factory=lambda: Path(
            _config.get("paths", {}).get("recording_dir", "data/recordings")
        ),
        alias="VLOG_RECORDING_DIR",
    )
    sample_rate: int = _config.get("audio", {}).get("sample_rate", 16000)
    channels: int = _config.get("audio", {}).get("channels", 1)
    block_size: int = _config.get("audio", {}).get("block_size", 1024)
    device_index: int | None = _config.get("audio", {}).get("device_index", None)
    device_name: str | None = _config.get("audio", {}).get("device_name", None)
    whisper_model_size: str = _config.get("whisper", {}).get("model_size", "large-v3")
    whisper_device: str = _config.get("whisper", {}).get("device", "cuda")
    whisper_compute_type: str = _config.get("whisper", {}).get(
        "compute_type", "float16"
    )
    huggingface_token: str | None = Field(default=None, alias="HUGGINGFACE_TOKEN")
    transcript_dir: Path = Field(
        default_factory=lambda: Path(
            _config.get("paths", {}).get("transcript_dir", "data/transcripts")
        ),
        alias="VLOG_TRANSCRIPT_DIR",
    )
    summary_dir: Path = Field(
        default_factory=lambda: Path(
            _config.get("paths", {}).get("summary_dir", "data/summaries")
        ),
        alias="VLOG_SUMMARY_DIR",
    )
    photo_prompt_dir: Path = Field(
        default_factory=lambda: Path(
            _config.get("paths", {}).get("photo_prompt_dir", "data/photos_prompts")
        ),
        alias="VLOG_PHOTO_PROMPT_DIR",
    )
    photo_dir: Path = Field(
        default_factory=lambda: Path(
            _config.get("paths", {}).get("photo_dir", "data/photos")
        ),
        alias="VLOG_PHOTO_DIR",
    )
    novel_out_dir: Path = Field(
        default_factory=lambda: Path(
            _config.get("novel", {}).get("out_dir", "data/novels")
        ),
        alias="VLOG_NOVEL_OUT_DIR",
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
    image_generator_default_prompt: str = "(masterpiece, best quality:1.2), anime scenery, highly detailed, expressive lighting, aesthetic, {text}"
    image_generator_default_negative_prompt: str = "low quality, worst quality, bad anatomy, vr, headset, holding controller, holding object, holding weapon, floating objects, weird objects"
    archive_after_process: bool = _config.get("processing", {}).get(
        "archive_after_process", True
    )
    archive_dir: Path = Field(
        default_factory=lambda: Path(
            _config.get("paths", {}).get("archive_dir", "data/archives")
        ),
        alias="VLOG_ARCHIVE_DIR",
    )
    trace_file: Path = Field(
        default_factory=lambda: Path(
            _config.get("paths", {}).get("trace_file", "data/traces.jsonl")
        ),
        alias="VLOG_TRACE_FILE",
    )
    prompts: Dict[str, Any] = _prompts

    @field_validator(
        "recording_dir",
        "transcript_dir",
        "summary_dir",
        "novel_out_dir",
        "photo_prompt_dir",
        "photo_dir",
        "archive_dir",
        mode="after",
    )
    @classmethod
    def validate_linux_paths(cls, v: Path, info) -> Path:
        if platform.system() != "Linux":
            return v
        s_path = str(v)
        if s_path.startswith("Z:") or "\\" in s_path:
            defaults = {
                "recording_dir": "data/recordings",
                "transcript_dir": "data/transcripts",
                "summary_dir": "data/summaries",
                "novel_out_dir": "data/novels",
                "photo_prompt_dir": "data/photos_prompts",
                "photo_dir": "data/photos",
                "archive_dir": "data/archives",
            }
            field_name = info.field_name
            default_val = _config.get("paths", {}).get(
                field_name, defaults.get(field_name)
            )
            if default_val:
                return Path(default_val)
        return v


settings = Settings()
