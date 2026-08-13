from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "packages" / "memory-domain" / "src"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "privacy" / "src"))

from vlog_memory_domain import (  # noqa: E402
    EvidenceRef,
    MemoryClaim,
    MemoryStatus,
    SocialMirrorEvidenceLevel,
    SocialMirrorValue,
)
from vlog_privacy import (  # noqa: E402
    SocialMirrorPublicationDecision,
    project_social_mirror_claim,
)

NOW = datetime(2026, 8, 13, 10, 30, tzinfo=timezone.utc)


def make_claim(
    *,
    speaker_label: str = "friend-a",
    speaker_entity_id: str | None = None,
    status: MemoryStatus = MemoryStatus.ACCEPTED,
) -> MemoryClaim:
    evidence = EvidenceRef(
        source_object_id=str(uuid4()),
        episode_id=str(uuid4()),
        utterance_id=str(uuid4()),
    )
    return MemoryClaim(
        claim_type="social_mirror",
        subject_entity_id=str(uuid4()),
        value=SocialMirrorValue(
            evidence_level=SocialMirrorEvidenceLevel.PARAPHRASE,
            text="詳しすぎると言われた",
            speaker_label=speaker_label,
            speaker_entity_id=speaker_entity_id,
        ),
        valid_from=NOW,
        evidence=(evidence,),
        status=status,
        confidence=0.9,
    )


def make_decision(
    claim: MemoryClaim,
    *,
    publish_text: bool = False,
    publish_speaker_identity: bool = False,
) -> SocialMirrorPublicationDecision:
    return SocialMirrorPublicationDecision(
        claim_id=claim.id,
        decided_at=NOW,
        decided_by="owner",
        rationale="explicit publication review",
        publish_text=publish_text,
        publish_speaker_identity=publish_speaker_identity,
    )


def test_social_mirror_publication_is_private_by_default() -> None:
    claim = make_claim()
    decision = make_decision(claim)

    assert decision.is_private is True
    assert decision.publish_text is False
    assert decision.publish_speaker_identity is False
    assert project_social_mirror_claim(claim, decision) is None


def test_text_can_be_published_without_speaker_identity() -> None:
    claim = make_claim(
        speaker_label="friend-a",
        speaker_entity_id=str(uuid4()),
    )
    decision = make_decision(claim, publish_text=True)

    projection = project_social_mirror_claim(claim, decision)

    assert projection is not None
    assert projection.text == "詳しすぎると言われた"
    assert projection.speaker_label is None
    assert projection.occurred_at == claim.valid_from
    assert projection.context is None
    assert projection.reaction is None


def test_speaker_identity_requires_its_own_explicit_decision() -> None:
    claim = make_claim(
        speaker_label="friend-a",
        speaker_entity_id=str(uuid4()),
    )
    decision = make_decision(
        claim,
        publish_text=True,
        publish_speaker_identity=True,
    )

    projection = project_social_mirror_claim(claim, decision)

    assert projection is not None
    assert projection.speaker_label == "friend-a"


def test_unknown_speaker_is_not_resolved_or_guessed() -> None:
    claim = make_claim(speaker_label="unknown")
    decision = make_decision(
        claim,
        publish_text=True,
        publish_speaker_identity=True,
    )

    projection = project_social_mirror_claim(claim, decision)

    assert projection is not None
    assert projection.speaker_label == "unknown"


def test_public_projection_excludes_raw_evidence_and_internal_speaker_id() -> None:
    claim = make_claim(
        speaker_label="friend-a",
        speaker_entity_id=str(uuid4()),
    )
    decision = make_decision(
        claim,
        publish_text=True,
        publish_speaker_identity=True,
    )

    projection = project_social_mirror_claim(claim, decision)
    assert projection is not None
    payload = asdict(projection)

    assert set(payload) == {
        "claim_id",
        "publication_decision_id",
        "evidence_level",
        "text",
        "speaker_label",
        "occurred_at",
        "published_at",
        "context",
        "reaction",
    }
    assert "evidence" not in payload
    assert "source_excerpt" not in payload
    assert "transcript" not in payload
    assert "speaker_entity_id" not in payload


def test_publication_decision_and_projection_trace_to_original_claim() -> None:
    claim = make_claim()
    decision = make_decision(claim, publish_text=True)

    projection = project_social_mirror_claim(claim, decision)

    assert projection is not None
    assert decision.claim_id == claim.id
    assert projection.claim_id == claim.id
    assert projection.publication_decision_id == decision.id


def test_mismatched_publication_decision_is_rejected() -> None:
    claim = make_claim()
    other_claim = make_claim()
    decision = make_decision(other_claim, publish_text=True)

    with pytest.raises(ValueError, match="reference the projected claim"):
        project_social_mirror_claim(claim, decision)


def test_candidate_claim_cannot_be_published() -> None:
    claim = make_claim(status=MemoryStatus.CANDIDATE)
    decision = make_decision(claim, publish_text=True)

    with pytest.raises(ValueError, match="only accepted"):
        project_social_mirror_claim(claim, decision)


def test_public_projection_schema_has_no_raw_source_fields() -> None:
    schema = json.loads(
        (
            REPO_ROOT / "schemas" / "social-mirror-public-projection.schema.json"
        ).read_text()
    )
    properties = set(schema["properties"])

    assert schema["additionalProperties"] is False
    assert properties == {
        "claim_id",
        "publication_decision_id",
        "evidence_level",
        "text",
        "speaker_label",
        "occurred_at",
        "published_at",
        "context",
        "reaction",
    }
    assert properties.isdisjoint(
        {
            "evidence",
            "source_object_id",
            "source_excerpt",
            "transcript",
            "speaker_entity_id",
        }
    )
