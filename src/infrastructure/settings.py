from pathlib import Path
from typing import Any, Dict, Set

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def load_config() -> Dict[str, Any]:
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


_config = load_config()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Gemini
    gemini_api_key: str = Field(alias="GOOGLE_API_KEY")
    gemini_model: str = _config.get("gemini", {}).get("model", "gemini-2.5-flash")
    novel_model: str = _config.get("novel", {}).get("model", "gemini-2.5-flash")
    novel_max_output_tokens: int = _config.get("novel", {}).get(
        "max_output_tokens", 8192
    )

    # Jules (Mini-Tasks)
    jules_api_key: str = Field(default="", alias="GOOGLE_JULES_API_KEY")
    jules_model: str = _config.get("jules", {}).get("model", "gemini-2.5-flash")

    # Supabase
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_service_role_key: str = Field(
        default="", alias="SUPABASE_SERVICE_ROLE_KEY"
    )

    # Application Loop
    check_interval: int = _config.get("process", {}).get("check_interval", 5)
    process_names: Set[str] = set(
        _config.get("process", {}).get("names", "VRChat").split(",")
    )

    # Audio Recording
    recording_dir: Path = Path(
        _config.get("paths", {}).get("recording_dir", "data/recordings")
    )
    sample_rate: int = _config.get("audio", {}).get("sample_rate", 16000)
    channels: int = _config.get("audio", {}).get("channels", 1)
    block_size: int = _config.get("audio", {}).get("block_size", 1024)

    # Whisper
    whisper_model_size: str = _config.get("whisper", {}).get("model_size", "large-v3")
    whisper_device: str = _config.get("whisper", {}).get("device", "cuda")
    whisper_compute_type: str = _config.get("whisper", {}).get(
        "compute_type", "float16"
    )
    transcript_dir: Path = Path(
        _config.get("paths", {}).get("transcript_dir", "data/transcripts")
    )

    # Summarization
    summary_dir: Path = Path(
        _config.get("paths", {}).get("summary_dir", "data/summaries")
    )

    photo_prompt_dir: Path = Path(
        _config.get("paths", {}).get("photo_prompt_dir", "data/photos_prompts")
    )
    photo_dir: Path = Path(_config.get("paths", {}).get("photo_dir", "data/photos"))

    # Novel
    novel_out_dir: Path = Path(_config.get("novel", {}).get("out_dir", "data/novels"))

    # Image Generation
    image_model: str = _config.get("image", {}).get(
        "model", "cagliostrolab/animagine-xl-3.1"
    )
    image_device: str = _config.get("image", {}).get("device", "cuda")
    image_height: int = _config.get("image", {}).get("height", 1024)
    image_width: int = _config.get("image", {}).get("width", 1024)
    image_num_inference_steps: int = _config.get("image", {}).get(
        "num_inference_steps", 28
    )
    image_guidance_scale: float = _config.get("image", {}).get("guidance_scale", 7.0)
    image_seed: int = _config.get("image", {}).get("seed", 42)
    image_generator_default_prompt: str = (
        "(masterpiece, best quality:1.2), anime style, {text}"
    )
    image_generator_default_negative_prompt: str = (
        "low quality, worst quality, bad anatomy"
    )

    # Archiving
    archive_after_process: bool = _config.get("processing", {}).get(
        "archive_after_process", True
    )
    archive_dir: Path = Path(
        _config.get("paths", {}).get("archive_dir", "data/archives")
    )


settings = Settings()
