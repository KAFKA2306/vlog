from __future__ import annotations

import os
import platform
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Mapping


class PathFlavor(StrEnum):
    RELATIVE = "relative"
    POSIX_ABSOLUTE = "posix_absolute"
    WINDOWS_ABSOLUTE = "windows_absolute"
    WINDOWS_DRIVE_RELATIVE = "windows_drive_relative"
    WINDOWS_UNC = "windows_unc"


_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")
_WINDOWS_DRIVE_RELATIVE_RE = re.compile(r"^[A-Za-z]:(?![\\/])")
_WSL_MOUNT_RE = re.compile(r"^/mnt/[A-Za-z](?:/|$)")


def classify_path(value: str | os.PathLike[str]) -> PathFlavor:
    """Classify a path lexically without touching the host filesystem."""

    text = os.fspath(value)
    windows = PureWindowsPath(text)
    if text.startswith("\\\\") and windows.is_absolute():
        return PathFlavor.WINDOWS_UNC
    if _WINDOWS_ABSOLUTE_RE.match(text):
        return PathFlavor.WINDOWS_ABSOLUTE
    if _WINDOWS_DRIVE_RELATIVE_RE.match(text):
        return PathFlavor.WINDOWS_DRIVE_RELATIVE
    if PurePosixPath(text).is_absolute():
        return PathFlavor.POSIX_ABSOLUTE
    return PathFlavor.RELATIVE


def foreign_absolute_reason(
    value: str | os.PathLike[str], *, system: str | None = None
) -> str | None:
    runtime = system or platform.system()
    flavor = classify_path(value)
    if runtime == "Linux" and flavor in {
        PathFlavor.WINDOWS_ABSOLUTE,
        PathFlavor.WINDOWS_UNC,
    }:
        return f"{flavor.value} is foreign to Linux/WSL"
    if runtime == "Windows" and flavor == PathFlavor.POSIX_ABSOLUTE:
        return "posix_absolute is foreign to Windows"
    return None


def shared_checkout_reason(
    value: str | os.PathLike[str], *, system: str | None = None
) -> str | None:
    """Return why a path is unsuitable as the canonical production checkout."""

    runtime = system or platform.system()
    text = os.fspath(value)
    flavor = classify_path(text)
    if runtime == "Linux" and flavor == PathFlavor.POSIX_ABSOLUTE:
        normalized = PurePosixPath(text).as_posix()
        if _WSL_MOUNT_RE.match(normalized):
            return "WSL runtime is using a Windows-mounted /mnt/<drive> checkout"
    if runtime == "Windows" and flavor == PathFlavor.WINDOWS_UNC:
        host = PureWindowsPath(text).parts[0].lower()
        if "wsl$" in host or "wsl.localhost" in host:
            return "Windows runtime is using a WSL UNC checkout"
        return "UNC checkout is not a canonical VLog production topology"
    return None


@dataclass(frozen=True)
class RuntimeDirectories:
    config: Path
    state: Path
    cache: Path


def runtime_directories(
    *,
    env: Mapping[str, str] | None = None,
    system: str | None = None,
    home: Path | None = None,
) -> RuntimeDirectories:
    """Resolve portable VLog config/state/cache homes without creating them."""

    values = os.environ if env is None else env
    runtime = system or platform.system()
    user_home = (home or Path.home()).expanduser()

    if runtime == "Windows":
        appdata = Path(values.get("APPDATA", user_home / "AppData/Roaming"))
        local = Path(values.get("LOCALAPPDATA", user_home / "AppData/Local"))
        config = Path(values.get("VLOG_CONFIG_HOME", appdata / "VLog"))
        state = Path(values.get("VLOG_STATE_HOME", local / "VLog/State"))
        cache = Path(values.get("VLOG_CACHE_HOME", local / "VLog/Cache"))
    else:
        config_base = Path(values.get("XDG_CONFIG_HOME", user_home / ".config"))
        state_base = Path(values.get("XDG_STATE_HOME", user_home / ".local/state"))
        cache_base = Path(values.get("XDG_CACHE_HOME", user_home / ".cache"))
        config = Path(values.get("VLOG_CONFIG_HOME", config_base / "vlog"))
        state = Path(values.get("VLOG_STATE_HOME", state_base / "vlog"))
        cache = Path(values.get("VLOG_CACHE_HOME", cache_base / "vlog"))

    return RuntimeDirectories(config=config, state=state, cache=cache)
