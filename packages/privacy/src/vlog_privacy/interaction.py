from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from vlog_memory_domain import INTERACTION_CLAIM_TYPES, MemoryClaim, MemoryStatus


def _new_id() -> str:
    return str(uuid4())


def _validate_id(value: str, field_name: str) -> None:
    try:
        UUID(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{field_name} must be a UUID string") from exc


@dataclass(frozen=True, slots=True)
class InteractionPublicationDecision:
    claim_id: str
    decided_at: datetime
    decided_by: str
    rationale: str
    publish: bool = False
    id: str = field(default_factory=_new_id)

    def __post_init__(self) -> None:
        _validate_id(self.id, "id")
        _validate_id(self.claim_id, "claim_id")
        if self.decided_at.tzinfo is None or self.decided_at.utcoffset() is None:
            raise ValueError("decided_at must be timezone-aware")
        if not self.decided_by.strip():
            raise ValueError("decided_by must not be empty")
        if not self.rationale.strip():
            raise ValueError("publication decisions require an explicit rationale")


@dataclass(frozen=True, slots=True)
class InteractionPublicProjection:
    claim_id: str
    publication_decision_id: str
    claim_type: str
    occurred_at: datetime
    published_at: datetime


def project_interaction_claim(
    claim: MemoryClaim, decision: InteractionPublicationDecision
) -> InteractionPublicProjection | None:
    if claim.id != decision.claim_id:
        raise ValueError("publication decision must reference the projected claim")
    if claim.claim_type not in INTERACTION_CLAIM_TYPES:
        raise ValueError("claim_type is not an interaction claim type")
    if claim.status is not MemoryStatus.ACCEPTED:
        raise ValueError("only accepted interaction claims may be published")
    if not decision.publish:
        return None
    return InteractionPublicProjection(
        claim_id=claim.id,
        publication_decision_id=decision.id,
        claim_type=claim.claim_type,
        occurred_at=claim.valid_from,
        published_at=decision.decided_at,
    )
