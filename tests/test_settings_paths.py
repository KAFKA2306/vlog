from pathlib import Path

import pytest
from vlog_capture.infrastructure.settings import (
    Settings,
    _settings_env_file,
    is_posix_path_invalid_on_windows,
    is_windows_path_invalid_on_linux,
    resolve_project_path,
)
from vlog_capture.project import PROJECT_ROOT


def test_resolve_project_path_anchors_relative_readonly_assets() -> None:
    assert resolve_project_path(Path("data/prompts.yaml")) == (
        PROJECT_ROOT / "data/prompts.yaml"
    )


def test_resolve_project_path_rejects_windows_drive_paths_in_wsl() -> None:
    with pytest.raises(ValueError, match="Windows path is not valid in WSL"):
        resolve_project_path(Path(r"Z:\home\kafka\projects\vlog\transcripts"))


def test_resolve_project_path_rejects_windows_unc_paths_in_wsl() -> None:
    with pytest.raises(ValueError, match="Windows path is not valid in WSL"):
        resolve_project_path(Path(r"\\wsl.localhost\Ubuntu-22.04\home\kafka"))


def test_settings_rejects_windows_paths_in_wsl() -> None:
    with pytest.raises(ValueError, match="Windows path is not valid in WSL"):
        Settings(
            VLOG_GEMINI_API_KEY="test",
            VLOG_RECORDING_DIR=r"Z:\home\kafka\projects\vlog\recordings",
        )


def test_relative_runtime_path_anchors_to_data_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_home = tmp_path / "runtime data"
    monkeypatch.setenv("VLOG_DATA_HOME", str(data_home))
    value = Settings(
        VLOG_GEMINI_API_KEY="test",
        VLOG_RECORDING_DIR="recordings",
    )
    assert value.recording_dir == data_home / "recordings"


def test_settings_use_one_environment_prefix() -> None:
    assert Settings.model_config["env_prefix"] == "VLOG_"


@pytest.mark.parametrize(
    ("retired_env", "canonical_env", "field"),
    [
        ("GOOGLE_API_KEY", "VLOG_GEMINI_API_KEY", "gemini_api_key"),
        ("GOOGLE_JULES_API_KEY", "VLOG_JULES_API_KEY", "jules_api_key"),
        ("SUPABASE_URL", "VLOG_SUPABASE_URL", "supabase_url"),
        (
            "SUPABASE_SERVICE_ROLE_KEY",
            "VLOG_SUPABASE_SERVICE_ROLE_KEY",
            "supabase_service_role_key",
        ),
        ("DISCORD_WEBHOOK_URL", "VLOG_DISCORD_WEBHOOK_URL", "discord_webhook_url"),
    ],
)
def test_retired_environment_aliases_are_ignored(
    monkeypatch: pytest.MonkeyPatch,
    retired_env: str,
    canonical_env: str,
    field: str,
) -> None:
    monkeypatch.delenv(canonical_env, raising=False)
    monkeypatch.setenv(retired_env, "retired-value")
    assert getattr(Settings(), field) == ""


def test_retired_error_event_alias_is_ignored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    retired_path = tmp_path / "retired.jsonl"
    monkeypatch.delenv("VLOG_ERROR_LOG_FILE", raising=False)
    monkeypatch.setenv("VLOG_ERROR_EVENT_FILE", str(retired_path))
    assert Settings().error_log_file != retired_path
    assert Settings().error_log_file.name == "error_events.jsonl"


def test_explicit_env_file_handles_space_hash_and_unicode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_home = tmp_path / "data-home"
    env_file = tmp_path / "config with space.env"
    env_file.write_text(
        'VLOG_RECORDING_DIR="録音 folder #1"\nVLOG_GEMINI_API_KEY="test-key"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("VLOG_DATA_HOME", str(data_home))
    monkeypatch.setenv("VLOG_ENV_FILE", str(env_file))
    value = Settings(_env_file=_settings_env_file(), _env_file_encoding="utf-8")
    assert value.recording_dir == data_home / "録音 folder #1"
    assert value.gemini_api_key == "test-key"


def test_env_file_must_be_absolute(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VLOG_ENV_FILE", "relative.env")
    with pytest.raises(RuntimeError, match="must be an absolute path"):
        _settings_env_file()


def test_windows_drive_path_guard_is_linux_only() -> None:
    value = Path(r"Z:\home\kafka\projects\vlog\transcripts")

    assert is_windows_path_invalid_on_linux(value, system="Linux")
    assert not is_windows_path_invalid_on_linux(value, system="Windows")


def test_posix_path_guard_is_windows_only() -> None:
    value = Path("/home/kafka/projects/vlog/transcripts")

    assert is_posix_path_invalid_on_windows(value, system="Windows")
    assert not is_posix_path_invalid_on_windows(value, system="Linux")
