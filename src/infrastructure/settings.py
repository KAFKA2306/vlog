import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    process_name: str
    process_names: tuple[str, ...]
    check_interval: int
    recording_dir: str
    diary_dir: str
    transcript_dir: str
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


def _load_yaml_config() -> dict:
    config_path = Path("config.yaml")
    if not config_path.exists():
        return {}
    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def _get_nested(config: dict, *keys: str, default=None):
    value = config
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return default
    return value if value is not None else default


def _env_str(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    return float(value)


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


def _process_names(primary: str | None, yaml_names: str) -> tuple[str, ...]:
    default = ("VRChat.exe", "VRChat", "VRChatClient.exe")
    raw = _env_str("VLOG_PROCESS_NAMES")
    if raw:
        parts = tuple(name.strip() for name in raw.split(",") if name.strip())
        names = parts or default
    elif yaml_names:
        parts = tuple(name.strip() for name in yaml_names.split(",") if name.strip())
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
    config = _load_yaml_config()

    process_name = _env_str("VLOG_PROCESS_NAME", "VRChat.exe") or "VRChat.exe"
    yaml_process_names = _get_nested(config, "process", "names", default="")

    return Settings(
        process_name=process_name,
        process_names=_process_names(process_name, yaml_process_names),
        check_interval=_env_int(
            "VLOG_CHECK_INTERVAL",
            _get_nested(config, "process", "check_interval", default=30),
        ),
        recording_dir=_env_str(
            "VLOG_RECORDING_DIR",
            _get_nested(
                config,
                "paths",
                "recording_dir",
                default=os.path.join(cwd, "recordings"),
            ),
        ),
        diary_dir=_env_str(
            "VLOG_DIARY_DIR",
            _get_nested(
                config, "paths", "diary_dir", default=os.path.join(cwd, "diaries")
            ),
        ),
        transcript_dir=_env_str(
            "VLOG_TRANSCRIPT_DIR",
            _get_nested(
                config,
                "paths",
                "transcript_dir",
                default=os.path.join(cwd, "transcripts"),
            ),
        ),
        sample_rate=_env_int(
            "VLOG_SAMPLE_RATE",
            _get_nested(config, "audio", "sample_rate", default=16000),
        ),
        channels=_env_int(
            "VLOG_CHANNELS", _get_nested(config, "audio", "channels", default=1)
        ),
        block_size=_env_int(
            "VLOG_BLOCK_SIZE", _get_nested(config, "audio", "block_size", default=1024)
        ),
        whisper_model_size=_env_str(
            "VLOG_WHISPER_MODEL_SIZE",
            _get_nested(config, "whisper", "model_size", default="base"),
        ),
        whisper_device=_env_str(
            "VLOG_WHISPER_DEVICE",
            _get_nested(config, "whisper", "device", default="cpu"),
        ),
        whisper_compute_type=_env_str(
            "VLOG_WHISPER_COMPUTE_TYPE",
            _get_nested(config, "whisper", "compute_type", default="int8"),
        ),
        whisper_beam_size=_env_int(
            "VLOG_WHISPER_BEAM_SIZE",
            _get_nested(config, "whisper", "beam_size", default=5),
        ),
        whisper_vad_filter=_env_bool(
            "VLOG_WHISPER_VAD_FILTER",
            _get_nested(config, "whisper", "vad_filter", default=True),
        ),
        gemini_model=_env_str(
            "VLOG_GEMINI_MODEL",
            _get_nested(config, "gemini", "model", default="gemini-2.0-flash-exp"),
        ),
        gemini_api_key_env=_env_str("VLOG_GEMINI_API_KEY_ENV", "GOOGLE_API_KEY"),
        gemini_api_key=_env_str("VLOG_GEMINI_API_KEY"),
        silence_threshold=_env_float(
            "VLOG_SILENCE_THRESHOLD",
            _get_nested(config, "audio", "silence_threshold", default=0.02),
        ),
        retention_days=_env_int(
            "VLOG_RETENTION_DAYS", _get_nested(config, "retention", "days", default=7)
        ),
    )


settings = _load_settings()
