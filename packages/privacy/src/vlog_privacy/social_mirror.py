from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from vlog_memory_domain import (
    SOCIAL_MIRROR_CLAIM_TYPE,
    MemoryClaim,
    MemoryStatus,
    SocialMirrorEvidenceLevel,
    SocialMirrorValue,
)


def _new_id() -> str:
    return str(uuid4())


def _validate_id(value: str, field_name: str) -> None:
    try:
        UUID(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{field_name} must be a UUID string") from exc


def _validate_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


@dataclass(frozen=True, slots=True)
class SocialMirrorPublicationDecision:
    """Explicit publication choices for one canonical Social Mirror claim.

    Both publication dimensions default to false. This keeps stored observations
    private until a deliberate decision is recorded, while allowing quote text
    and speaker identity to be approved independently.
    """

    claim_id: str
    decided_at: datetime
    decided_by: str
    rationale: str
    publish_text: bool = False
    publish_speaker_identity: bool = False
    id: str = field(default_factory=_new_id)

    def __post_init__(self) -> None:
        _validate_id(self.id, "id")
        _validate_id(self.claim_id, "claim_id")
        _validate_aware(self.decided_at, "decided_at")
        if not self.decided_by.strip():
            raise ValueError("decided_by must not be empty")
        if not self.rationale.strip():
            raise ValueError("publication decisions require an explicit rationale")

    @property
    def is_private(self) -> bool:
        return not self.publish_text and not self.publish_speaker_identity


@dataclass(frozen=True, slots=True)
class SocialMirrorPublicProjection:
    """Rebuildable public view with no raw EvidenceRef or transcript content."""

    claim_id: str
    publication_decision_id: str
    evidence_level: SocialMirrorEvidenceLevel
    text: str
    speaker_label: str | None
    published_at: datetime


def project_social_mirror_claim(
    claim: MemoryClaim,
    decision: SocialMirrorPublicationDecision,
) -> SocialMirrorPublicProjection | None:
    """Apply publication policy without reading private raw evidence.

    The function consumes only an already-canonical claim and its explicit
    publication decision. It never accepts transcript text, source excerpts, or
    entity lookup services, which prevents the public projection step from
    expanding an unknown speaker into a guessed identity.
    """

    if claim.id != decision.claim_id:
        raise ValueError("publication decision must reference the projected claim")
    if claim.claim_type != SOCIAL_MIRROR_CLAIM_TYPE:
        raise ValueError("claim_type must be 'social_mirror'")
    if not isinstance(claim.value, SocialMirrorValue):
        raise ValueError("social_mirror claims require a SocialMirrorValue")
    if claim.status is not MemoryStatus.ACCEPTED:
        raise ValueError("only accepted Social Mirror claims may be published")

    if not decision.publish_text:
        return None

    speaker_label = None
    if decision.publish_speaker_identity:
        speaker_label = claim.value.speaker_label

    return SocialMirrorPublicProjection(
        claim_id=claim.id,
        publication_decision_id=decision.id,
        evidence_level=claim.value.evidence_level,
        text=claim.value.text,
        speaker_label=speaker_label,
        published_at=decision.decided_at,
    )
