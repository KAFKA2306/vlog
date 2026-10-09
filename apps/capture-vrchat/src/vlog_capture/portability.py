from __future__ import annotations

import os
import platform
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Mapping

from platformdirs import PlatformDirs


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
    data: Path
    state: Path
    cache: Path


def _explicit_runtime_directories(
    values: Mapping[str, str], *, runtime: str, user_home: Path
) -> RuntimeDirectories:
    if runtime == "Windows":
        appdata = Path(values.get("APPDATA", user_home / "AppData/Roaming"))
        local = Path(values.get("LOCALAPPDATA", user_home / "AppData/Local"))
        config = Path(values.get("VLOG_CONFIG_HOME", appdata / "VLog"))
        data = Path(values.get("VLOG_DATA_HOME", local / "VLog/Data"))
        state = Path(values.get("VLOG_STATE_HOME", local / "VLog/State"))
        cache = Path(values.get("VLOG_CACHE_HOME", local / "VLog/Cache"))
    else:
        config_base = Path(values.get("XDG_CONFIG_HOME", user_home / ".config"))
        data_base = Path(values.get("XDG_DATA_HOME", user_home / ".local/share"))
        state_base = Path(values.get("XDG_STATE_HOME", user_home / ".local/state"))
        cache_base = Path(values.get("XDG_CACHE_HOME", user_home / ".cache"))
        config = Path(values.get("VLOG_CONFIG_HOME", config_base / "vlog"))
        data = Path(values.get("VLOG_DATA_HOME", data_base / "vlog"))
        state = Path(values.get("VLOG_STATE_HOME", state_base / "vlog"))
        cache = Path(values.get("VLOG_CACHE_HOME", cache_base / "vlog"))
    return RuntimeDirectories(config=config, data=data, state=state, cache=cache)


def runtime_directories(
    *,
    env: Mapping[str, str] | None = None,
    system: str | None = None,
    home: Path | None = None,
) -> RuntimeDirectories:
    """Resolve VLog config/data/state/cache homes without creating them.

    The real host follows platformdirs. Explicit `env`/`system`/`home` arguments use
    the equivalent deterministic rules so Windows and Linux behavior can be tested
    from either CI host.
    """

    values = os.environ if env is None else env
    if env is not None or system is not None or home is not None:
        return _explicit_runtime_directories(
            values,
            runtime=system or platform.system(),
            user_home=(home or Path.home()).expanduser(),
        )

    dirs = PlatformDirs(appname="vlog", appauthor=False, roaming=True)
    defaults = RuntimeDirectories(
        config=Path(dirs.user_config_dir),
        data=Path(PlatformDirs(appname="vlog", appauthor=False).user_data_dir),
        state=Path(dirs.user_state_dir),
        cache=Path(dirs.user_cache_dir),
    )
    return RuntimeDirectories(
        config=Path(values.get("VLOG_CONFIG_HOME", defaults.config)),
        data=Path(values.get("VLOG_DATA_HOME", defaults.data)),
        state=Path(values.get("VLOG_STATE_HOME", defaults.state)),
        cache=Path(values.get("VLOG_CACHE_HOME", defaults.cache)),
    )
