import os
from dataclasses import dataclass


@dataclass
class Settings:
    process_name: str = "VRChat.exe"
    check_interval: int = 30
    recording_dir: str = os.path.join(os.getcwd(), "recordings")
    diary_dir: str = os.path.join(os.getcwd(), "diaries")
    sample_rate: int = 44100
    channels: int = 1
    block_size: int = 1024
    whisper_model_size: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"


settings = Settings()
