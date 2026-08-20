from pathlib import Path

import pytest
from vlog_capture.infrastructure.settings import (
    Settings,
    _get_project_root,
    is_posix_path_invalid_on_windows,
    is_windows_path_invalid_on_linux,
    resolve_project_path,
)


def test_resolve_project_path_anchors_relative_paths() -> None:
    assert resolve_project_path(Path("data/recordings")) == (
        _get_project_root() / "data/recordings"
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
            GOOGLE_API_KEY="test",
            VLOG_RECORDING_DIR=r"Z:\home\kafka\projects\vlog\recordings",
        )


def test_windows_drive_path_guard_is_linux_only() -> None:
    value = Path(r"Z:\home\kafka\projects\vlog\transcripts")

    assert is_windows_path_invalid_on_linux(value, system="Linux")
    assert not is_windows_path_invalid_on_linux(value, system="Windows")


def test_posix_path_guard_is_windows_only() -> None:
    value = Path("/home/kafka/projects/vlog/transcripts")

    assert is_posix_path_invalid_on_windows(value, system="Windows")
    assert not is_posix_path_invalid_on_windows(value, system="Linux")
