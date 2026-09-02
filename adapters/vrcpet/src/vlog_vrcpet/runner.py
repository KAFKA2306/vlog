from __future__ import annotations

import json
import os
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from .normalizer import normalize_source
from .parser import parse_observation
from .reader import discover_source_paths, read_source_file, validate_source_root

PIPELINE_VERSION = "human-memory-v2:vrcpet-autonomous-1"


@dataclass(frozen=True, slots=True)
class IngestSummary:
    run_id: str
    status: str
    discovered: int
    ingested: int
    skipped: int
    failed: int
    parse_issues: int
    output_path: Path

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "discovered": self.discovered,
            "ingested": self.ingested,
            "skipped": self.skipped,
            "failed": self.failed,
            "parse_issues": self.parse_issues,
        }


def _path_from_env(name: str, default: Path | None = None) -> Path | None:
    value = os.environ.get(name)
    if value:
        return Path(value).expanduser().resolve()
    return default.resolve() if default is not None else None


def _private_root(data_root: Path, project_root: Path) -> Path:
    configured = _path_from_env("VLOG_PRIVATE_EVIDENCE_ROOT")
    root = configured or (data_root / "private-evidence").resolve()
    if not root.is_absolute():
        raise ValueError("VLOG_PRIVATE_EVIDENCE_ROOT must be absolute")
    if root == project_root or project_root in root.parents:
        raise ValueError("private evidence root must be outside the repository")
    return root


def _state_root() -> Path:
    configured = _path_from_env("VLOG_STATE_HOME")
    if configured is not None:
        return configured
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
        return (base / "VLog" / "State").resolve()
    base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
    return (base / "vlog").resolve()


def _data_root() -> Path:
    configured = _path_from_env("VLOG_DATA_HOME")
    if configured is not None:
        return configured
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
        return (base / "VLog" / "Data").resolve()
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return (base / "vlog").resolve()


def _append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _persist_raw(
    raw: bytes, *, private_root: Path, observation_type: str, digest: str
) -> None:
    destination = private_root / "vrcpet" / observation_type / digest[:2] / digest
    if destination.is_file():
        if (
            destination.stat().st_size != len(raw)
            or sha256(destination.read_bytes()).hexdigest() != digest
        ):
            raise IOError("private evidence object has an unexpected digest")
        return
    _atomic_write(destination, raw)


def _load_completed(ledger_path: Path, pipeline_version: str) -> set[str]:
    completed: set[str] = set()
    if not ledger_path.is_file():
        return completed
    for line_number, line in enumerate(
        ledger_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"invalid VRCPet ledger JSON at line {line_number}: {ledger_path}"
            ) from exc
        if (
            payload.get("status") == "succeeded"
            and payload.get("pipeline_version") == pipeline_version
            and isinstance(payload.get("source_hash"), str)
        ):
            completed.add(payload["source_hash"])
    return completed


def _safe_issue_codes(issues: tuple[Any, ...]) -> list[str]:
    return sorted({str(issue.code) for issue in issues})


def run_ingest(
    *,
    source_root: str | Path | None = None,
    project_root: str | Path | None = None,
    data_root: str | Path | None = None,
    state_root: str | Path | None = None,
    private_root: str | Path | None = None,
    run_id: str | None = None,
    pipeline_version: str = PIPELINE_VERSION,
    dry_run: bool = False,
) -> IngestSummary:
    effective_run_id = run_id or str(uuid4())
    repository = Path(project_root or os.environ.get("VLOG_PROJECT_ROOT", Path.cwd()))
    repository = repository.expanduser().resolve()
    effective_data = (
        Path(data_root).expanduser().resolve() if data_root else _data_root()
    )
    effective_state = (
        Path(state_root).expanduser().resolve() if state_root else _state_root()
    )
    run_dir = effective_state / "vrcpet" / "runs"
    output_path = run_dir / f"{effective_run_id}.json"

    configured_root = source_root or os.environ.get("VLOG_VRCPET_ROOT")
    if not configured_root:
        raise ValueError("VRCPet source root is required; set VLOG_VRCPET_ROOT")
    root = validate_source_root(configured_root)

    paths = discover_source_paths(root)
    ledger_path = effective_state / "vrcpet" / "ledger.jsonl"
    completed = _load_completed(ledger_path, pipeline_version)
    if dry_run:
        private_evidence_root = None
    elif private_root is not None:
        configured_private_root = Path(private_root).expanduser().resolve()
        if not configured_private_root.is_absolute():
            raise ValueError("private evidence root must be absolute")
        if (
            configured_private_root == repository
            or repository in configured_private_root.parents
        ):
            raise ValueError("private evidence root must be outside the repository")
        private_evidence_root = configured_private_root
    else:
        private_evidence_root = _private_root(effective_data, repository)
    ingested = skipped = parse_issues = 0

    for relative_path in paths:
        source = read_source_file(root, relative_path)
        if source.size_bytes == 0:
            skipped += 1
            continue

        parsed = parse_observation(source.relative_path, source.raw_bytes)
        parse_issues += len(parsed.issues)
        observation = normalize_source(source, parsed)
        digest = observation.source_hash
        if digest in completed:
            skipped += 1
            continue

        if private_evidence_root is not None:
            _persist_raw(
                source.raw_bytes,
                private_root=private_evidence_root,
                observation_type=parsed.observation_type,
                digest=digest,
            )
        manifest = dict(observation.manifest)
        manifest["metadata"] = dict(manifest["metadata"])
        manifest["metadata"].update(
            {
                "record_count": len(parsed.records),
                "parse_issue_codes": _safe_issue_codes(parsed.issues),
                "pipeline_version": pipeline_version,
            }
        )
        manifest_path = (
            effective_state
            / "vrcpet"
            / "manifests"
            / f"{observation.source_object.id}.json"
        )
        _atomic_write(
            manifest_path,
            json.dumps(manifest, ensure_ascii=False, sort_keys=True).encode(),
        )
        if not dry_run:
            _append_jsonl(
                ledger_path,
                {
                    "run_id": effective_run_id,
                    "source_object_id": observation.source_object.id,
                    "source_hash": digest,
                    "pipeline_version": pipeline_version,
                    "status": "succeeded",
                    "kind": observation.source_object.kind.value,
                    "observation_type": parsed.observation_type,
                    "source_relative_path": source.relative_path,
                    "record_count": len(parsed.records),
                    "parse_issue_codes": _safe_issue_codes(parsed.issues),
                    "recorded_at": observation.manifest["recorded_at"],
                },
            )
            completed.add(digest)
        ingested += 1

    summary = IngestSummary(
        effective_run_id,
        "succeeded",
        len(paths),
        ingested,
        skipped,
        0,
        parse_issues,
        output_path,
    )
    _atomic_write(output_path, json.dumps(summary.as_dict(), sort_keys=True).encode())
    return summary
