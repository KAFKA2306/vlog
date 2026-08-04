from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

_DEFAULT_ROOTS = (
    "data/recordings",
    "data/transcripts",
    "data/summaries",
    "data/novels",
    "data/photos",
    "data/evaluations",
    "data/manga",
)


@dataclass(frozen=True, slots=True)
class InventoryConfig:
    repo_root: Path
    evidence_roots: tuple[str, ...] = _DEFAULT_ROOTS
    hash_chunk_bytes: int = 1024 * 1024

    def __post_init__(self) -> None:
        if not self.repo_root.is_absolute():
            raise ValueError("repo_root must be absolute")
        if self.hash_chunk_bytes <= 0:
            raise ValueError("hash_chunk_bytes must be positive")
        for root in self.evidence_roots:
            candidate = Path(root)
            if candidate.is_absolute() or ".." in candidate.parts:
                raise ValueError(f"evidence root must be repository-relative: {root}")


@dataclass(frozen=True, slots=True)
class InventoryFile:
    category: str
    path: str
    size_bytes: int
    modified_at: str
    sha256: str
    tracked_by_git: bool
    is_symlink: bool
    link_target: str | None


class InventoryBuilder:
    """Build a read-only inventory of existing local evidence and artifacts."""

    def __init__(self, config: InventoryConfig) -> None:
        self.config = config

    def build(self) -> dict[str, object]:
        tracked = self._tracked_files()
        records = sorted(
            self._iter_records(tracked),
            key=lambda record: (record.category, record.path),
        )
        duplicate_hashes = self._duplicate_hashes(records)
        category_totals: dict[str, dict[str, int]] = {}
        for record in records:
            totals = category_totals.setdefault(
                record.category,
                {"files": 0, "bytes": 0, "tracked_files": 0},
            )
            totals["files"] += 1
            totals["bytes"] += record.size_bytes
            totals["tracked_files"] += int(record.tracked_by_git)

        return {
            "schema_version": "phase0-inventory-v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "repository": {
                "root": str(self.config.repo_root),
                "git_commit": self._git_commit(),
            },
            "policy": {
                "operation": "read-only",
                "deletes_files": False,
                "moves_files": False,
                "uploads_files": False,
                "hash_algorithm": "sha256",
            },
            "roots": list(self.config.evidence_roots),
            "summary": {
                "files": len(records),
                "bytes": sum(record.size_bytes for record in records),
                "tracked_files": sum(record.tracked_by_git for record in records),
                "categories": category_totals,
                "duplicate_hash_groups": len(duplicate_hashes),
            },
            "duplicate_hashes": duplicate_hashes,
            "files": [asdict(record) for record in records],
        }

    def _iter_records(self, tracked: set[str]) -> Iterable[InventoryFile]:
        for relative_root in self.config.evidence_roots:
            root = self.config.repo_root / relative_root
            if not root.exists():
                continue
            category = Path(relative_root).name
            for path in sorted(root.rglob("*")):
                if path.is_dir():
                    continue
                relative_path = path.relative_to(self.config.repo_root).as_posix()
                is_symlink = path.is_symlink()
                link_target = os.readlink(path) if is_symlink else None
                stat = path.lstat() if is_symlink else path.stat()
                digest = (
                    self._hash_symlink(link_target)
                    if is_symlink
                    else self._sha256(path)
                )
                yield InventoryFile(
                    category=category,
                    path=relative_path,
                    size_bytes=stat.st_size,
                    modified_at=datetime.fromtimestamp(
                        stat.st_mtime,
                        tz=timezone.utc,
                    ).isoformat(),
                    sha256=digest,
                    tracked_by_git=relative_path in tracked,
                    is_symlink=is_symlink,
                    link_target=link_target,
                )

    def _sha256(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            while chunk := stream.read(self.config.hash_chunk_bytes):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _hash_symlink(link_target: str | None) -> str:
        return hashlib.sha256((link_target or "").encode("utf-8")).hexdigest()

    def _tracked_files(self) -> set[str]:
        result = subprocess.run(
            ["git", "-C", str(self.config.repo_root), "ls-files", "-z"],
            check=False,
            capture_output=True,
        )
        if result.returncode != 0:
            return set()
        return {
            item.decode("utf-8", errors="surrogateescape")
            for item in result.stdout.split(b"\0")
            if item
        }

    def _git_commit(self) -> str | None:
        result = subprocess.run(
            ["git", "-C", str(self.config.repo_root), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() if result.returncode == 0 else None

    @staticmethod
    def _duplicate_hashes(records: list[InventoryFile]) -> list[dict[str, object]]:
        by_hash: dict[str, list[str]] = {}
        for record in records:
            by_hash.setdefault(record.sha256, []).append(record.path)
        return [
            {"sha256": digest, "paths": sorted(paths)}
            for digest, paths in sorted(by_hash.items())
            if len(paths) > 1
        ]


def write_inventory(inventory: dict[str, object], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(f"{output.suffix}.tmp")
    temporary.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(output)
