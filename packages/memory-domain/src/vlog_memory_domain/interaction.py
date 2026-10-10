from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import Any, Iterable, Mapping
from uuid import NAMESPACE_URL, UUID, uuid5

from .models import EvidenceRef, MemoryClaim, MemoryRevision, MemoryStatus, Utterance

SELF_EMOTION_CLAIM_TYPE = "self_emotion"
INTERACTION_UTTERANCE_CLAIM_TYPE = "interaction_utterance"
INTERACTION_RESPONSE_CLAIM_TYPE = "interaction_response"
RELATIONSHIP_CLAIM_TYPE = "relationship"
OPEN_LOOP_CLAIM_TYPE = "open_loop"

INTERACTION_CLAIM_TYPES = frozenset(
    {
        SELF_EMOTION_CLAIM_TYPE,
        INTERACTION_UTTERANCE_CLAIM_TYPE,
        INTERACTION_RESPONSE_CLAIM_TYPE,
        RELATIONSHIP_CLAIM_TYPE,
    }
)


class EmotionOrigin(StrEnum):
    SELF_EXPLICIT = "self_explicit"
    AI_INFERRED = "ai_inferred"


class IdentityState(StrEnum):
    CONFIRMED = "confirmed"
    UNCERTAIN = "uncertain"
    UNKNOWN = "unknown"


class ResponseKind(StrEnum):
    SPOKEN = "spoken"
    EXPLICIT_ACTION = "explicit_action"
    INFERRED_INNER_STATE = "inferred_inner_state"


class TimelineEntryKind(StrEnum):
    SELF_EMOTION = "self_emotion"
    INTERACTION = "interaction"
    RESPONSE = "response"
    OPEN_LOOP = "open_loop"
    RELATIONSHIP_REVISION = "relationship_revision"
    RELATIONSHIP = "relationship"


def _check_uuid(value: str, field_name: str) -> None:
    try:
        UUID(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{field_name} must be a UUID string") from exc


def _check_confidence(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _check_identity(state: IdentityState, entity_id: str | None, role: str) -> None:
    if state is IdentityState.CONFIRMED:
        if entity_id is None:
            raise ValueError(f"confirmed {role} requires an entity id")
        _check_uuid(entity_id, f"{role}_entity_id")
    elif entity_id is not None:
        raise ValueError(
            f"{role}_entity_id is only allowed when the {role} is confirmed"
        )


@dataclass(frozen=True, slots=True)
class SelfEmotionValue:
    origin: EmotionOrigin
    label: str
    intent: str | None = None

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ValueError("emotion label must not be empty")


@dataclass(frozen=True, slots=True)
class InteractionUtteranceValue:
    speaker_state: IdentityState
    target_state: IdentityState
    speaker_entity_id: str | None = None
    target_entity_id: str | None = None
    speaker_confidence: float = 1.0
    target_confidence: float = 1.0

    def __post_init__(self) -> None:
        _check_identity(self.speaker_state, self.speaker_entity_id, "speaker")
        _check_identity(self.target_state, self.target_entity_id, "target")
        _check_confidence(self.speaker_confidence, "speaker_confidence")
        _check_confidence(self.target_confidence, "target_confidence")


@dataclass(frozen=True, slots=True)
class ResponseValue:
    kind: ResponseKind
    responder_entity_id: str
    in_reply_to_claim_id: str

    def __post_init__(self) -> None:
        _check_uuid(self.responder_entity_id, "responder_entity_id")
        _check_uuid(self.in_reply_to_claim_id, "in_reply_to_claim_id")


@dataclass(frozen=True, slots=True)
class RelationshipValue:
    other_entity_id: str
    relation: str
    supersedes_claim_id: str | None = None

    def __post_init__(self) -> None:
        _check_uuid(self.other_entity_id, "other_entity_id")
        if not self.relation.strip():
            raise ValueError("relation must not be empty")
        if self.supersedes_claim_id is not None:
            _check_uuid(self.supersedes_claim_id, "supersedes_claim_id")


@dataclass(frozen=True, slots=True)
class TimelineEntry:
    kind: TimelineEntryKind
    at: datetime
    claim_id: str
    status: MemoryStatus
    evidence: tuple[EvidenceRef, ...]
    revision_id: str | None = None


_TIMELINE_RANK = {kind: index for index, kind in enumerate(TimelineEntryKind)}


def _canonical(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    return value


def deterministic_claim_id(
    claim_type: str,
    subject_entity_id: str,
    evidence: Iterable[EvidenceRef],
    value: Any,
) -> str:
    payload = json.dumps(
        {
            "claim_type": claim_type,
            "subject": subject_entity_id,
            "evidence": [asdict(ref) for ref in evidence],
            "value": _canonical(value),
        },
        sort_keys=True,
        default=str,
    )
    return str(uuid5(NAMESPACE_URL, f"vlog:interaction-claim:{payload}"))


def ingest_claims(
    existing: Iterable[MemoryClaim], incoming: Iterable[MemoryClaim]
) -> tuple[MemoryClaim, ...]:
    merged = {claim.id: claim for claim in existing}
    order = list(merged)
    for claim in incoming:
        known = merged.get(claim.id)
        if known is None:
            merged[claim.id] = claim
            order.append(claim.id)
        elif known != claim:
            raise ValueError(f"conflict: claim {claim.id} already exists differently")
    return tuple(merged[claim_id] for claim_id in order)


def _dereference(
    claim: MemoryClaim, utterances_by_id: Mapping[str, Utterance]
) -> tuple[Utterance, ...]:
    if not claim.evidence:
        raise ValueError(f"{claim.claim_type} claims require provenance evidence")
    found = []
    for ref in claim.evidence:
        if ref.utterance_id is None or ref.start_ms is None:
            raise ValueError("evidence must identify an utterance and source span")
        utterance = utterances_by_id.get(ref.utterance_id)
        if utterance is None or utterance.episode_id != ref.episode_id:
            raise ValueError("evidence must reference a raw utterance in its episode")
        found.append(utterance)
    return tuple(found)


def _expect(claim: MemoryClaim, value_type: type) -> Any:
    if not isinstance(claim.value, value_type):
        raise ValueError(f"{claim.claim_type} claims require a {value_type.__name__}")
    return claim.value


def validate_interaction_claim(
    claim: MemoryClaim, *, utterances_by_id: Mapping[str, Utterance]
) -> None:
    accepted = claim.status is MemoryStatus.ACCEPTED
    if claim.claim_type == SELF_EMOTION_CLAIM_TYPE:
        emotion = _expect(claim, SelfEmotionValue)
        if emotion.origin is EmotionOrigin.AI_INFERRED:
            if accepted:
                raise ValueError("AI-inferred emotion cannot be accepted")
            _dereference(claim, utterances_by_id)
            return
        for utterance in _dereference(claim, utterances_by_id):
            if utterance.speaker_entity_id != claim.subject_entity_id:
                raise ValueError("explicit emotion must come from a self utterance")
    elif claim.claim_type == INTERACTION_UTTERANCE_CLAIM_TYPE:
        spoken = _expect(claim, InteractionUtteranceValue)
        for utterance in _dereference(claim, utterances_by_id):
            if (
                spoken.speaker_state is IdentityState.CONFIRMED
                and utterance.speaker_entity_id is not None
                and utterance.speaker_entity_id != spoken.speaker_entity_id
            ):
                raise ValueError("confirmed speaker must match the raw utterance")
    elif claim.claim_type == INTERACTION_RESPONSE_CLAIM_TYPE:
        response = _expect(claim, ResponseValue)
        if response.kind is ResponseKind.INFERRED_INNER_STATE and accepted:
            raise ValueError("inferred inner state cannot be accepted as fact")
        utterances = _dereference(claim, utterances_by_id)
        if response.kind is ResponseKind.SPOKEN:
            for utterance in utterances:
                if utterance.speaker_entity_id != response.responder_entity_id:
                    raise ValueError("spoken response must come from the responder")
    elif claim.claim_type == RELATIONSHIP_CLAIM_TYPE:
        _expect(claim, RelationshipValue)
        _dereference(claim, utterances_by_id)
    else:
        raise ValueError(f"unsupported interaction claim_type: {claim.claim_type}")


def revise_relationship(
    previous: MemoryClaim,
    successor: MemoryClaim,
    *,
    revised_at: datetime,
    reason: str,
) -> tuple[MemoryClaim, MemoryRevision]:
    old = _expect(previous, RelationshipValue)
    new = _expect(successor, RelationshipValue)
    if not successor.evidence:
        raise ValueError("relationship revision requires new evidence")
    if previous.status is not MemoryStatus.ACCEPTED:
        raise ValueError("only an accepted relationship can be superseded")
    if (
        previous.subject_entity_id != successor.subject_entity_id
        or old.other_entity_id != new.other_entity_id
    ):
        raise ValueError("revision must concern the same entity pair")
    value = replace(new, supersedes_claim_id=previous.id)
    linked = replace(
        successor,
        value=value,
        id=deterministic_claim_id(
            successor.claim_type,
            successor.subject_entity_id,
            successor.evidence,
            value,
        ),
    )
    revision = MemoryRevision(
        claim_id=previous.id,
        previous_status=MemoryStatus.ACCEPTED,
        new_status=MemoryStatus.SUPERSEDED,
        reason=reason,
        revised_at=revised_at,
        evidence=successor.evidence,
    )
    return linked, revision


def _involves(claim: MemoryClaim, person_entity_id: str) -> TimelineEntryKind | None:
    value = claim.value
    subject = claim.subject_entity_id == person_entity_id
    if claim.claim_type == SELF_EMOTION_CLAIM_TYPE:
        return TimelineEntryKind.SELF_EMOTION if subject else None
    if claim.claim_type == INTERACTION_UTTERANCE_CLAIM_TYPE:
        if subject or person_entity_id in (
            value.speaker_entity_id,
            value.target_entity_id,
        ):
            return TimelineEntryKind.INTERACTION
    if claim.claim_type == INTERACTION_RESPONSE_CLAIM_TYPE:
        if subject or value.responder_entity_id == person_entity_id:
            return TimelineEntryKind.RESPONSE
    if claim.claim_type == RELATIONSHIP_CLAIM_TYPE:
        if subject or value.other_entity_id == person_entity_id:
            return TimelineEntryKind.RELATIONSHIP
    if claim.claim_type == OPEN_LOOP_CLAIM_TYPE and claim.valid_to is None:
        linked = (
            isinstance(value, Mapping) and value.get("entity_id") == person_entity_id
        )
        if subject or linked:
            return TimelineEntryKind.OPEN_LOOP
    return None


def retrieve_person_timeline(
    claims: Iterable[MemoryClaim],
    revisions: Iterable[MemoryRevision],
    person_entity_id: str,
) -> tuple[TimelineEntry, ...]:
    hidden = {MemoryStatus.REJECTED, MemoryStatus.FORGOTTEN}
    entries: list[TimelineEntry] = []
    relationship_ids: set[str] = set()
    for claim in claims:
        if claim.status in hidden:
            continue
        kind = _involves(claim, person_entity_id)
        if kind is None:
            continue
        if kind is TimelineEntryKind.RELATIONSHIP:
            relationship_ids.add(claim.id)
        entries.append(
            TimelineEntry(
                kind, claim.valid_from, claim.id, claim.status, claim.evidence
            )
        )
    for revision in revisions:
        if revision.claim_id in relationship_ids:
            entries.append(
                TimelineEntry(
                    TimelineEntryKind.RELATIONSHIP_REVISION,
                    revision.revised_at,
                    revision.claim_id,
                    revision.new_status,
                    revision.evidence,
                    revision_id=revision.id,
                )
            )
    entries.sort(key=lambda e: (e.at, _TIMELINE_RANK[e.kind], e.claim_id))
    return tuple(entries)
