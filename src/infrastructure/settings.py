import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    process_name: str
    process_names: tuple[str, ...]
    check_interval: int
    recording_dir: str
    diary_dir: str
    sample_rate: int
    channels: int
    block_size: int
    whisper_model_size: str
    whisper_device: str
    whisper_compute_type: str
    whisper_beam_size: int
    whisper_vad_filter: bool
    gemini_model: str
    gemini_api_key_env: str
    gemini_api_key: str | None
    silence_threshold: float
    retention_days: int


def _env_str(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _process_names(primary: str | None) -> tuple[str, ...]:
    default = ("VRChat.exe", "VRChat", "VRChatClient.exe")
    raw = _env_str("VLOG_PROCESS_NAMES")
    names: tuple[str, ...]
    if raw:
        parts = tuple(name.strip() for name in raw.split(",") if name.strip())
        names = parts or default
    else:
        names = default
    if primary:
        lowered = primary.lower()
        ordered = [primary]
        ordered.extend(name for name in names if name.lower() != lowered)
        return tuple(ordered)
    return names


def _load_settings() -> Settings:
    cwd = os.getcwd()
    process_name = _env_str("VLOG_PROCESS_NAME", "VRChat.exe") or "VRChat.exe"
    return Settings(
        process_name=process_name,
        process_names=_process_names(process_name),
        check_interval=_env_int("VLOG_CHECK_INTERVAL", 30),
        recording_dir=_env_str("VLOG_RECORDING_DIR", os.path.join(cwd, "recordings")),
        diary_dir=_env_str("VLOG_DIARY_DIR", os.path.join(cwd, "diaries")),
        sample_rate=_env_int("VLOG_SAMPLE_RATE", 16000),
        channels=_env_int("VLOG_CHANNELS", 1),
        block_size=_env_int("VLOG_BLOCK_SIZE", 1024),
        whisper_model_size=_env_str("VLOG_WHISPER_MODEL_SIZE", "base"),
        whisper_device=_env_str("VLOG_WHISPER_DEVICE", "cpu"),
        whisper_compute_type=_env_str("VLOG_WHISPER_COMPUTE_TYPE", "int8"),
        whisper_beam_size=_env_int("VLOG_WHISPER_BEAM_SIZE", 5),
        whisper_vad_filter=_env_bool("VLOG_WHISPER_VAD_FILTER", True),
        gemini_model=_env_str("VLOG_GEMINI_MODEL", "gemini-3-pro-preview"),
        gemini_api_key_env=_env_str("VLOG_GEMINI_API_KEY_ENV", "GOOGLE_API_KEY"),
        gemini_api_key=_env_str("VLOG_GEMINI_API_KEY"),
        silence_threshold=_env_float("VLOG_SILENCE_THRESHOLD", 0.02),
        retention_days=_env_int("VLOG_RETENTION_DAYS", 7),
    )


settings = _load_settings()
