from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "packages" / "memory-domain" / "src"))

from vlog_memory_domain import (  # noqa: E402
    EvidenceRef,
    IngestionRun,
    IngestionStatus,
    MemoryClaim,
    MemoryStatus,
    PrivacyLevel,
    SourceKind,
    SourceObject,
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


def test_ingestion_idempotency_key_includes_pipeline_version() -> None:
    run = IngestionRun(
        source_hash="abc123",
        pipeline_version="memory-v2.0.1",
        status=IngestionStatus.SUCCEEDED,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )

    assert run.idempotency_key == "abc123:memory-v2.0.1"
