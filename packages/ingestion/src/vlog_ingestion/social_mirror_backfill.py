from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

from vlog_memory_domain import (
    EvidenceRef,
    MemoryClaim,
    SocialMirrorEvidenceLevel,
    SocialMirrorValue,
    Utterance,
    validate_social_mirror_claim,
)

_QUOTED_SPAN = re.compile(r"「([^」\n]{1,240})」")


class BackfillSourceKind(StrEnum):
    RAW_TRANSCRIPT = "raw_transcript"
    SUMMARY = "summary"
    DIARY = "diary"


class SpeakerKind(StrEnum):
    SELF = "self"
    OTHER = "other"
    UNKNOWN = "unknown"


class BackfillCandidateStatus(StrEnum):
    VERIFIED_QUOTE_CANDIDATE = "verified_quote_candidate"
    REVIEW_CANDIDATE = "review_candidate"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class BackfillSourceRecord:
    """One immutable source record inspected by the dry-run backfill.

    `speaker_kind` expresses an already-known channel boundary. The backfill
    never infers a speaker from prose style or content.
    """

    source_object_id: str
    episode_id: str
    recorded_at: datetime
    source_kind: BackfillSourceKind
    text: str
    utterance_id: str | None = None
    speaker_kind: SpeakerKind = SpeakerKind.UNKNOWN
    speaker_label: str = "unknown"


@dataclass(frozen=True, slots=True)
class BackfillCandidate:
    candidate_id: str
    source_object_id: str
    episode_id: str
    recorded_at: datetime
    source_kind: BackfillSourceKind
    status: BackfillCandidateStatus
    reason: str
    text: str | None = None
    speaker_label: str = "unknown"
    suggested_evidence_level: SocialMirrorEvidenceLevel | None = None


@dataclass(frozen=True, slots=True)
class BackfillReport:
    candidates: tuple[BackfillCandidate, ...]

    @property
    def total_sources(self) -> int:
        return len({item.source_object_id for item in self.candidates})

    @property
    def verified_count(self) -> int:
        return sum(
            item.status is BackfillCandidateStatus.VERIFIED_QUOTE_CANDIDATE
            for item in self.candidates
        )

    @property
    def review_count(self) -> int:
        return sum(
            item.status is BackfillCandidateStatus.REVIEW_CANDIDATE
            for item in self.candidates
        )

    @property
    def skipped_count(self) -> int:
        return sum(
            item.status is BackfillCandidateStatus.SKIPPED for item in self.candidates
        )


def _stable_candidate_id(
    source: BackfillSourceRecord,
    *,
    text: str | None,
    reason: str,
) -> str:
    material = "\x1f".join(
        [
            source.source_object_id,
            source.episode_id,
            source.source_kind.value,
            source.utterance_id or "",
            source.speaker_kind.value,
            source.speaker_label,
            text or "",
            reason,
        ]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _candidate(
    source: BackfillSourceRecord,
    *,
    status: BackfillCandidateStatus,
    reason: str,
    text: str | None = None,
    suggested_evidence_level: SocialMirrorEvidenceLevel | None = None,
) -> BackfillCandidate:
    return BackfillCandidate(
        candidate_id=_stable_candidate_id(source, text=text, reason=reason),
        source_object_id=source.source_object_id,
        episode_id=source.episode_id,
        recorded_at=source.recorded_at,
        source_kind=source.source_kind,
        status=status,
        reason=reason,
        text=text,
        speaker_label=source.speaker_label,
        suggested_evidence_level=suggested_evidence_level,
    )


def _inspect_raw_transcript(source: BackfillSourceRecord) -> tuple[BackfillCandidate, ...]:
    text = source.text.strip()
    if not text:
        return (
            _candidate(
                source,
                status=BackfillCandidateStatus.SKIPPED,
                reason="empty_source",
            ),
        )

    if source.speaker_kind is SpeakerKind.SELF:
        return (
            _candidate(
                source,
                status=BackfillCandidateStatus.SKIPPED,
                reason="speaker_is_self",
            ),
        )

    if source.speaker_kind is not SpeakerKind.OTHER:
        return (
            _candidate(
                source,
                status=BackfillCandidateStatus.REVIEW_CANDIDATE,
                reason="speaker_boundary_unverified",
                text=text,
                suggested_evidence_level=SocialMirrorEvidenceLevel.PARAPHRASE,
            ),
        )

    if source.utterance_id is None:
        return (
            _candidate(
                source,
                status=BackfillCandidateStatus.REVIEW_CANDIDATE,
                reason="missing_utterance_trace",
                text=text,
                suggested_evidence_level=SocialMirrorEvidenceLevel.PARAPHRASE,
            ),
        )

    evidence = EvidenceRef(
        source_object_id=source.source_object_id,
        episode_id=source.episode_id,
        utterance_id=source.utterance_id,
    )
    claim = MemoryClaim(
        claim_type="social_mirror",
        subject_entity_id=source.episode_id,
        value=SocialMirrorValue(
            evidence_level=SocialMirrorEvidenceLevel.DIRECT_QUOTE,
            text=text,
            speaker_label=source.speaker_label,
        ),
        valid_from=source.recorded_at,
        evidence=(evidence,),
    )
    utterance = Utterance(
        id=source.utterance_id,
        episode_id=source.episode_id,
        started_at=source.recorded_at,
        ended_at=source.recorded_at,
        text=source.text,
    )
    validate_social_mirror_claim(
        claim,
        utterances_by_id={source.utterance_id: utterance},
    )

    return (
        _candidate(
            source,
            status=BackfillCandidateStatus.VERIFIED_QUOTE_CANDIDATE,
            reason="raw_utterance_verbatim_match",
            text=text,
            suggested_evidence_level=SocialMirrorEvidenceLevel.DIRECT_QUOTE,
        ),
    )


def _inspect_derived(source: BackfillSourceRecord) -> tuple[BackfillCandidate, ...]:
    quoted_spans = tuple(match.group(1).strip() for match in _QUOTED_SPAN.finditer(source.text))
    quoted_spans = tuple(span for span in quoted_spans if span)
    if not quoted_spans:
        return (
            _candidate(
                source,
                status=BackfillCandidateStatus.SKIPPED,
                reason="no_explicit_quote_marker",
            ),
        )

    return tuple(
        _candidate(
            source,
            status=BackfillCandidateStatus.REVIEW_CANDIDATE,
            reason=f"{source.source_kind.value}_derived_quote_marker",
            text=span,
            suggested_evidence_level=SocialMirrorEvidenceLevel.PARAPHRASE,
        )
        for span in quoted_spans
    )


def dry_run_social_mirror_backfill(
    sources: tuple[BackfillSourceRecord, ...],
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> BackfillReport:
    """Return deterministic candidates without persisting any claim.

    Date boundaries are inclusive. Sources outside the requested range are not
    returned because they were not inspected by this run.
    """

    if start_date is not None and end_date is not None and start_date > end_date:
        raise ValueError("start_date must be <= end_date")

    inspected: list[BackfillCandidate] = []
    ordered_sources = sorted(
        sources,
        key=lambda source: (
            source.recorded_at,
            source.source_object_id,
            source.source_kind.value,
        ),
    )
    for source in ordered_sources:
        source_date = source.recorded_at.date()
        if start_date is not None and source_date < start_date:
            continue
        if end_date is not None and source_date > end_date:
            continue

        if source.source_kind is BackfillSourceKind.RAW_TRANSCRIPT:
            inspected.extend(_inspect_raw_transcript(source))
        else:
            inspected.extend(_inspect_derived(source))

    return BackfillReport(candidates=tuple(inspected))
