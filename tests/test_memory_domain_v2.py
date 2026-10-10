from __future__ import annotations

import hashlib
from dataclasses import asdict, fields
from datetime import datetime, timezone
from pathlib import PurePosixPath, PureWindowsPath
from uuid import uuid4

import pytest
from vlog_memory_domain import (
    EvidenceRef,
    IngestionRun,
    IngestionStatus,
    MemoryClaim,
    MemoryStatus,
    PrivacyLevel,
    SourceKind,
    SourceObject,
    validate_source_manifest,
    verify_source_hash,
)


def test_accepted_claim_requires_provenance() -> None:
    with pytest.raises(ValueError, match="require provenance"):
        MemoryClaim(
            claim_type="preference",
            subject_entity_id=str(uuid4()),
            value="quiet hotels",
            valid_from=datetime.now(timezone.utc),
            evidence=(),
            status=MemoryStatus.ACCEPTED,
        )


def test_accepted_claim_retains_episode_and_source_reference() -> None:
    evidence = EvidenceRef(
        source_object_id=str(uuid4()),
        episode_id=str(uuid4()),
        utterance_id=str(uuid4()),
        start_ms=1200,
        end_ms=4300,
    )
    claim = MemoryClaim(
        claim_type="open_loop",
        subject_entity_id=str(uuid4()),
        value={"task": "confirm booking"},
        valid_from=datetime.now(timezone.utc),
        evidence=(evidence,),
        status=MemoryStatus.ACCEPTED,
        confidence=0.9,
    )

    assert claim.evidence == (evidence,)
    assert claim.status is MemoryStatus.ACCEPTED


def test_private_source_requires_private_object_uri() -> None:
    with pytest.raises(ValueError, match="private://"):
        SourceObject(
            kind=SourceKind.AUDIO,
            object_uri="https://example.invalid/session.flac",
            sha256="0" * 64,
            size_bytes=123,
            recorded_at=datetime.now(timezone.utc),
            privacy=PrivacyLevel.PRIVATE,
        )


@pytest.mark.parametrize(
    "local_locator",
    [
        r"C:\\Users\\kafka\\VLog\\recordings\\session.flac",
        "/home/kafka/vlog/recordings/session.flac",
        "file:///home/kafka/vlog/recordings/session.flac",
    ],
)
def test_source_object_rejects_machine_local_locator(local_locator: str) -> None:
    with pytest.raises(ValueError, match="machine-local"):
        SourceObject(
            kind=SourceKind.AUDIO,
            object_uri=local_locator,
            sha256="a" * 64,
            size_bytes=123,
            recorded_at=datetime.now(timezone.utc),
            privacy=PrivacyLevel.PUBLIC,
        )


def test_evidence_identity_survives_windows_and_wsl_materialization_paths() -> None:
    source_id = str(uuid4())
    recorded_at = datetime.now(timezone.utc)
    canonical = {
        "kind": SourceKind.AUDIO,
        "object_uri": "private://evidence/sha256/" + "a" * 64,
        "sha256": "a" * 64,
        "size_bytes": 4096,
        "recorded_at": recorded_at,
        "privacy": PrivacyLevel.PRIVATE,
        "id": source_id,
    }

    windows_materialization = PureWindowsPath(r"D:\\VLogData\\recordings\\session.flac")
    wsl_materialization = PurePosixPath(
        "/home/kafka/.local/share/VLog/recordings/session.flac"
    )
    assert windows_materialization != wsl_materialization

    windows_view = SourceObject(**canonical)
    wsl_view = SourceObject(**canonical)
    assert windows_view == wsl_view
    assert windows_view.id == source_id
    assert windows_view.sha256 == "a" * 64
    assert all("path" not in item.name.lower() for item in fields(SourceObject))
    assert all("path" not in key.lower() for key in asdict(windows_view))


def test_ingestion_requires_sha256_and_pipeline_version() -> None:
    digest = "b" * 64
    run = IngestionRun(
        source_hash=digest,
        pipeline_version="memory-v2.0.1",
        status=IngestionStatus.SUCCEEDED,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )

    assert run.idempotency_key == f"{digest}:memory-v2.0.1"

    with pytest.raises(ValueError, match="64-character"):
        IngestionRun(
            source_hash="abc123",
            pipeline_version="memory-v2.0.1",
            status=IngestionStatus.PENDING,
            started_at=datetime.now(timezone.utc),
        )


def _manifest(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": str(uuid4()),
        "kind": "audio",
        "object_uri": "private://evidence/sha256/" + "a" * 64,
        "sha256": "a" * 64,
        "size_bytes": 4,
        "recorded_at": "2026-01-01T00:00:00+00:00",
        "privacy": "private",
        "original_filename": "session.flac",
        "metadata": {"source": "x", "source_relative_path": "logs/a.jsonl"},
    }
    return base | overrides


def test_source_manifest_accepts_path_free_metadata() -> None:
    validate_source_manifest(_manifest())


@pytest.mark.parametrize(
    "overrides",
    [
        {"metadata": {"p": r"C:\Users\kafka\a.flac"}},
        {"metadata": {"nested": {"p": "/home/kafka/a.flac"}}},
        {"metadata": {"items": ["file:///home/kafka/a.flac"]}},
        {"metadata": {"p": "../escape/a.flac"}},
        {"original_filename": "dir/session.flac"},
        {"original_filename": r"C:\x\session.flac"},
        {"object_uri": "/home/kafka/a.flac"},
    ],
)
def test_source_manifest_rejects_machine_local_paths(
    overrides: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        validate_source_manifest(_manifest(**overrides))


def test_source_manifest_requires_sha256() -> None:
    manifest = _manifest()
    del manifest["sha256"]
    with pytest.raises(ValueError, match="sha256"):
        validate_source_manifest(manifest)


def test_verify_source_hash_is_location_independent() -> None:
    data = b"evidence"
    source = SourceObject(
        kind=SourceKind.DOCUMENT,
        object_uri="private://evidence/sha256/x",
        sha256=hashlib.sha256(data).hexdigest(),
        size_bytes=len(data),
        recorded_at=datetime.now(timezone.utc),
    )
    verify_source_hash(source, data)
    with pytest.raises(ValueError, match="sha256 mismatch"):
        verify_source_hash(source, b"tampered")
    with pytest.raises(ValueError, match="size"):
        verify_source_hash(source, data + b"!")
