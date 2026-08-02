from pathlib import Path

import pytest

from src.infrastructure.settings import (
    Settings,
    _get_project_root,
    resolve_project_path,
)


def test_resolve_project_path_anchors_relative_paths() -> None:
    assert resolve_project_path(Path("data/recordings")) == (
        _get_project_root() / "data/recordings"
    )


def test_resolve_project_path_rejects_windows_paths_in_wsl() -> None:
    with pytest.raises(ValueError, match="Windows path is not valid in WSL"):
        resolve_project_path(Path(r"\\wsl.localhost\Ubuntu-22.04\home\kafka"))


def test_settings_rejects_windows_paths_in_wsl() -> None:
    with pytest.raises(ValueError, match="Windows path is not valid in WSL"):
        Settings(
            GOOGLE_API_KEY="test",
            VLOG_RECORDING_DIR=r"\\wsl.localhost\Ubuntu-22.04\home\kafka",
        )
