from pathlib import Path
from typing import Set

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Gemini
    gemini_api_key: str = Field(alias="GOOGLE_API_KEY")
    gemini_model: str = "gemini-1.5-flash"
    novel_model: str = "gemini-1.5-flash"
    novel_max_output_tokens: int = 8192

    # Supabase
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_service_role_key: str = Field(
        default="", alias="SUPABASE_SERVICE_ROLE_KEY"
    )

    # Application Loop
    check_interval: int = 5
    process_names: Set[str] = {"VRChat"}

    # Audio Recording
    recording_dir: Path = Path("data/recordings")
    sample_rate: int = 16000
    channels: int = 1
    block_size: int = 1024

    # Whisper
    whisper_model_size: str = "large-v3"
    whisper_device: str = "cuda"
    whisper_compute_type: str = "float16"
    transcript_dir: Path = Path("data/transcripts")

    # Summarization
    summary_dir: Path = Path("data/summaries")

    # Novel
    novel_out_dir: Path = Path("data/novels")

    # Image Generation
    image_model: str = "cagliostrolab/animagine-xl-3.1"
    image_height: int = 1024
    image_width: int = 1024
    image_num_inference_steps: int = 28
    image_guidance_scale: float = 7.0
    image_seed: int = 42
    image_generator_default_prompt: str = (
        "(masterpiece, best quality:1.2), anime style, {text}"
    )
    image_generator_default_negative_prompt: str = (
        "low quality, worst quality, bad anatomy"
    )

    # Archiving
    archive_after_process: bool = True
    archive_dir: Path = Path("data/archives")


settings = Settings()
