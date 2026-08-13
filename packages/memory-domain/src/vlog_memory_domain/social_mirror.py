from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping
from uuid import UUID

from .models import MemoryClaim, Utterance

SOCIAL_MIRROR_CLAIM_TYPE = "social_mirror"
UNKNOWN_SPEAKER = "unknown"


class SocialMirrorEvidenceLevel(StrEnum):
    """How strongly a Social Mirror claim is supported as speech evidence."""

    DIRECT_QUOTE = "direct_quote"
    PARAPHRASE = "paraphrase"
    INFERRED_IMPRESSION = "inferred_impression"


@dataclass(frozen=True, slots=True)
class SocialMirrorValue:
    """Typed value stored inside a canonical ``MemoryClaim``.

    This is a value object, not a separate canonical store. The enclosing
    ``MemoryClaim`` continues to own time, status, confidence, and EvidenceRef
    provenance.
    """

    evidence_level: SocialMirrorEvidenceLevel
    text: str
    speaker_label: str
    speaker_entity_id: str | None = None

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("social mirror text must not be empty")
        if not self.speaker_label.strip():
            raise ValueError(
                "speaker_label must not be empty; use 'unknown' when unknown"
            )
        if self.speaker_entity_id is not None:
            try:
                UUID(self.speaker_entity_id)
            except (ValueError, TypeError) as exc:
                raise ValueError("speaker_entity_id must be a UUID string") from exc

    @property
    def is_verbatim(self) -> bool:
        return self.evidence_level is SocialMirrorEvidenceLevel.DIRECT_QUOTE

    @property
    def is_spoken_fact(self) -> bool:
        """Whether this value represents speech rather than an interpretation."""

        return self.evidence_level in {
            SocialMirrorEvidenceLevel.DIRECT_QUOTE,
            SocialMirrorEvidenceLevel.PARAPHRASE,
        }


def validate_social_mirror_claim(
    claim: MemoryClaim,
    *,
    utterances_by_id: Mapping[str, Utterance] | None = None,
) -> None:
    """Validate Social Mirror semantics against canonical evidence.

    JSON Schema can validate the shape of a Social Mirror value, but it cannot
    dereference EvidenceRef objects into raw utterance text. This function is
    the domain-level evidence gate used before a candidate is treated according
    to its declared evidence level.

    ``direct_quote`` requires the exact text to occur in a referenced raw
    ``Utterance`` whose episode matches the EvidenceRef. A quotation mark in a
    summary, diary, Novel, or other derived artifact therefore cannot promote a
    claim to ``direct_quote`` without raw utterance evidence.
    """

    if claim.claim_type != SOCIAL_MIRROR_CLAIM_TYPE:
        raise ValueError("claim_type must be 'social_mirror'")
    if not isinstance(claim.value, SocialMirrorValue):
        raise ValueError("social_mirror claims require a SocialMirrorValue")
    if not claim.evidence:
        raise ValueError("social_mirror claims require provenance evidence")

    value = claim.value
    if value.evidence_level is not SocialMirrorEvidenceLevel.DIRECT_QUOTE:
        return

    if utterances_by_id is None:
        raise ValueError("direct_quote validation requires raw utterance evidence")

    referenced_utterance = False
    for evidence_ref in claim.evidence:
        if evidence_ref.utterance_id is None:
            continue
        utterance = utterances_by_id.get(evidence_ref.utterance_id)
        if utterance is None:
            continue
        if utterance.episode_id != evidence_ref.episode_id:
            continue
        referenced_utterance = True
        if value.text in utterance.text:
            return

    if not referenced_utterance:
        raise ValueError("direct_quote requires a referenced raw utterance")
    raise ValueError("direct_quote text must appear verbatim in referenced raw evidence")
