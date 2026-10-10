from __future__ import annotations

import ctypes
import os
import platform
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

PACKAGES = ("nvidia.cublas", "nvidia.cudnn")
WSL_NATIVE_DIR = Path("/usr/lib/wsl/lib")


class GpuLibraryError(RuntimeError):
    pass


@dataclass(frozen=True)
class Resolution:
    package: str
    directory: Path | None
    libraries: tuple[str, ...]


def _package_dir(name: str, search_path: Sequence[str]) -> Path | None:
    relative = Path(*name.split("."))
    for entry in search_path:
        candidate = Path(entry or ".") / relative
        if candidate.is_dir():
            return candidate
    return None


def discover(
    *,
    search_path: Sequence[str] | None = None,
    system: str | None = None,
) -> list[Resolution]:
    paths = list(sys.path if search_path is None else search_path)
    subdir = "bin" if (system or platform.system()) == "Windows" else "lib"
    found = []
    for package in PACKAGES:
        root = _package_dir(package, paths)
        directory = root / subdir if root is not None else None
        if directory is None or not directory.is_dir():
            found.append(Resolution(package, None, ()))
            continue
        found.append(
            Resolution(
                package, directory, tuple(sorted(p.name for p in directory.iterdir()))
            )
        )
    return found


def require(found: Sequence[Resolution]) -> None:
    missing = [item.package for item in found if item.directory is None]
    if missing:
        raise GpuLibraryError(
            "pip-provided CUDA libraries not found: "
            + ", ".join(missing)
            + " (install nvidia-cublas-cu12 / nvidia-cudnn-cu12)"
        )


def ld_library_path(
    found: Sequence[Resolution], *, existing: str = "", system: str | None = None
) -> str:
    separator = ";" if (system or platform.system()) == "Windows" else ":"
    current = [part for part in existing.split(separator) if part]
    additions = [
        str(item.directory)
        for item in found
        if item.directory is not None and str(item.directory) not in current
    ]
    return separator.join(additions + current)


def wsl_native_cuda(directory: Path = WSL_NATIVE_DIR) -> Path | None:
    candidate = directory / "libcuda.so.1"
    return candidate if candidate.exists() else None


def report(found: Sequence[Resolution], *, native: Path | None) -> str:
    lines = [
        f"{item.package}: {item.directory} [{', '.join(item.libraries)}]"
        if item.directory is not None
        else f"{item.package}: MISSING"
        for item in found
    ]
    lines.append(
        f"wsl-native-cuda: {native}"
        if native is not None
        else "wsl-native-cuda: UNAVAILABLE"
    )
    return "\n".join(lines)


def prepare_environment() -> list[Resolution]:
    found = discover()
    print(report(found, native=wsl_native_cuda()), file=sys.stderr)
    require(found)
    for item in found:
        if platform.system() == "Windows":
            os.add_dll_directory(str(item.directory))
            continue
        for name in item.libraries:
            if ".so" in name:
                ctypes.CDLL(str(item.directory / name), mode=ctypes.RTLD_GLOBAL)
    return found
