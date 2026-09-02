from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


class SourceBoundaryError(ValueError):
    """Raised when a source path escapes the configured read-only boundary."""


class UnstableSourceError(RuntimeError):
    """Raised when a source changes while it is being read."""


@dataclass(frozen=True, slots=True)
class SourceFile:
    relative_path: str
    raw_bytes: bytes
    size_bytes: int
    mtime_ns: int


def _contains(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return True


def validate_source_root(
    root: str | Path,
    *,
    allowlisted_roots: Iterable[str | Path] = (),
) -> Path:
    resolved = Path(root).expanduser().resolve(strict=True)
    if not resolved.is_dir():
        raise SourceBoundaryError("VRCPet source root must be a directory")

    allowed = tuple(
        Path(item).expanduser().resolve(strict=True) for item in allowlisted_roots
    )
    if allowed and not any(_contains(base, resolved) for base in allowed):
        raise SourceBoundaryError("VRCPet source root is outside the allowlist")
    return resolved


def discover_source_paths(root: str | Path) -> tuple[str, ...]:
    source_root = Path(root)
    discovered: set[str] = set()

    logs_dir = source_root / "logs"
    if logs_dir.is_dir():
        for path in logs_dir.rglob("*.jsonl"):
            if path.is_file():
                discovered.add(path.relative_to(source_root).as_posix())

    for filename in ("pet.log", "profile.json", "heard_nouns.json"):
        path = source_root / filename
        if path.is_file():
            discovered.add(filename)

    return tuple(sorted(discovered))


def read_source_file(
    root: str | Path,
    relative_path: str | Path,
    *,
    allowlisted_roots: Iterable[str | Path] = (),
) -> SourceFile:
    source_root = validate_source_root(root, allowlisted_roots=allowlisted_roots)
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise SourceBoundaryError("source path must be relative to the configured root")

    path = (source_root / relative).resolve(strict=True)
    if not _contains(source_root, path) or not path.is_file():
        raise SourceBoundaryError("source file escapes the configured root")

    before = path.stat()
    raw_bytes = path.read_bytes()
    after = path.stat()
    if (
        before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
        or len(raw_bytes) != after.st_size
    ):
        raise UnstableSourceError(
            f"source changed while reading: {relative.as_posix()}"
        )

    return SourceFile(
        relative_path=relative.as_posix(),
        raw_bytes=raw_bytes,
        size_bytes=len(raw_bytes),
        mtime_ns=after.st_mtime_ns,
    )
