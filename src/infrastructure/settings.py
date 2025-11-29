import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    check_interval: int
    recording_dir: str
    transcript_dir: str
    summary_dir: str
    archive_dir: str
    sample_rate: int
    channels: int
    block_size: int
    whisper_model_size: str
    whisper_device: str
    whisper_compute_type: str
    gemini_model: str
    gemini_api_key: str | None
    archive_after_process: bool
    process_names: tuple[str, ...]
    novel_enabled: bool
    novel_out_dir: str
    novel_model: str
    novel_max_output_tokens: int
    config: dict


def _load_settings() -> Settings:
    if not Path("config.yaml").exists():
        raise FileNotFoundError(
            "config.yaml not found. It is required for configuration."
        )

    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    return Settings(
        check_interval=config["process"]["check_interval"],
        recording_dir=config["paths"]["recording_dir"],
        transcript_dir=config["paths"]["transcript_dir"],
        summary_dir=config["paths"]["summary_dir"],
        archive_dir=config["paths"]["archive_dir"],
        sample_rate=config["audio"]["sample_rate"],
        channels=config["audio"]["channels"],
        block_size=config["audio"]["block_size"],
        whisper_model_size=config["whisper"]["model_size"],
        whisper_device=config["whisper"]["device"],
        whisper_compute_type=config["whisper"]["compute_type"],
        gemini_model=config["gemini"]["model"],
        gemini_api_key=os.getenv("VLOG_GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY")),
        archive_after_process=config["processing"]["archive_after_process"],
        process_names=tuple(config["process"]["names"].split(",")),
        novel_enabled=config.get("novel", {}).get("enabled", False),
        novel_out_dir=config.get("novel", {}).get("out_dir", "data/novels"),
        novel_model=config.get("novel", {}).get("model", "gemini-2.5-flash"),
        novel_max_output_tokens=config.get("novel", {}).get("max_output_tokens", 4096),
        config=config,
    )


settings = _load_settings()
