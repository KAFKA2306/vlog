#!/usr/bin/env python3
"""Copy legacy repo-local VLog runtime data to OS-standard runtime homes.

The migration is intentionally non-destructive: sources are never removed. Existing
identical targets are accepted; conflicting targets fail. Every applied run writes a
manifest containing source/target paths, byte sizes, and SHA-256 values.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from vlog_capture.portability import RuntimeDirectories, runtime_directories
from vlog_capture.project import PROJECT_ROOT

DATA_DIRS = {
    "recordings",
    "transcripts",
    "summaries",
    "novels",
    "photos",
    "photos_prompts",
    "evaluations",
    "manga",
    "archives",
    "sync_reports",
}
STATE_DIRS = {"logs", "heartbeats", "reports"}
STATE_FILES = {
    "error_events.jsonl",
    "incidents.jsonl",
    "daily_runs.jsonl",
    "traces.jsonl",
}
CONFIG_FILES = {"profile.yaml"}
VERSIONED_FILES = {"config.yaml", "prompts.yaml"}


@dataclass(frozen=True, slots=True)
class MigrationRecord:
    source: str
    target: str
    category: str
    size_bytes: int
    sha256: str
    action: str


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def target_for(relative: Path, homes: RuntimeDirectories) -> tuple[str, Path] | None:
    if relative.parts[0] in DATA_DIRS:
        return "data", homes.data / relative
    if relative.parts[0] in STATE_DIRS:
        return "state", homes.state / relative
    if len(relative.parts) == 1 and relative.name in STATE_FILES:
        return "state", homes.state / relative.name
    if len(relative.parts) == 1 and relative.name in CONFIG_FILES:
        return "config", homes.config / relative.name
    if len(relative.parts) == 1 and relative.name in VERSIONED_FILES:
        return None
    return "data", homes.data / "legacy" / relative


def plan(
    source_root: Path,
    homes: RuntimeDirectories,
    *,
    apply: bool,
) -> list[MigrationRecord]:
    records: list[MigrationRecord] = []
    if not source_root.exists():
        return records

    for source in sorted(path for path in source_root.rglob("*") if path.is_file()):
        relative = source.relative_to(source_root)
        resolved = target_for(relative, homes)
        if resolved is None:
            continue
        category, target = resolved
        source_hash = sha256(source)
        action = "copy"
        if target.exists():
            target_hash = sha256(target)
            if target_hash != source_hash:
                raise RuntimeError(
                    f"target conflict: {target} differs from legacy source {source}"
                )
            action = "already-identical"
        elif apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            if sha256(target) != source_hash:
                target.unlink(missing_ok=True)
                raise RuntimeError(f"hash verification failed after copy: {target}")

        records.append(
            MigrationRecord(
                source=str(source),
                target=str(target),
                category=category,
                size_bytes=source.stat().st_size,
                sha256=source_hash,
                action=action if apply else f"would-{action}",
            )
        )
    return records


def write_manifest(records: list[MigrationRecord], homes: RuntimeDirectories) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest = homes.state / "migrations" / f"repo-data-{timestamp}.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_deleted": False,
        "records": [asdict(record) for record in records],
        "files": len(records),
        "bytes": sum(record.size_bytes for record in records),
    }
    manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=PROJECT_ROOT / "data")
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    homes = runtime_directories()
    records = plan(args.source.expanduser().resolve(), homes, apply=args.apply)
    for record in records:
        print(
            f"{record.action}: {record.source} -> {record.target} "
            f"({record.size_bytes} bytes, sha256={record.sha256})"
        )
    if args.apply:
        manifest = write_manifest(records, homes)
        print(f"manifest: {manifest}")
    else:
        print("dry-run: no files were copied or deleted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
