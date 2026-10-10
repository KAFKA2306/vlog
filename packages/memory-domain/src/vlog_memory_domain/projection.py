from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from typing import Any, Protocol

from .models import Episode, EvidenceRef, MemoryClaim, MemoryStatus, Utterance

DEFAULT_MIN_TEXT_CHARS = 10


class ProjectionStatus(StrEnum):
    PROJECTED = "projected"
    DUPLICATE = "duplicate"
    SKIPPED = "skipped"
    REJECTED = "rejected"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class EpisodeCandidate:
    """Canonical records for one session, as read from the canonical store."""

    episode: Episode
    utterances: tuple[Utterance, ...]
    claims: tuple[MemoryClaim, ...]
    source_hash: str
    pipeline_version: str


@dataclass(frozen=True, slots=True)
class ProjectionFact:
    claim_id: str
    claim_type: str
    value: Any
    valid_from: datetime
    valid_to: datetime | None
    confidence: float
    evidence: tuple[EvidenceRef, ...]


@dataclass(frozen=True, slots=True)
class EpisodeProjectionPayload:
    """Vendor-neutral, rebuildable projection of exactly one canonical episode."""

    episode_id: str
    reference_time: datetime
    body: str
    facts: tuple[ProjectionFact, ...]
    evidence: tuple[EvidenceRef, ...]
    source_hash: str
    pipeline_version: str
    projection_version: str

    @property
    def projection_key(self) -> str:
        material = ":".join(
            (
                self.episode_id,
                self.source_hash,
                self.pipeline_version,
                self.projection_version,
            )
        )
        return sha256(material.encode("utf-8")).hexdigest()

    @property
    def episode_name(self) -> str:
        return f"vlog:episode:{self.episode_id}"

    @property
    def source_description(self) -> str:
        return (
            f"vlog episode={self.episode_id} source_hash={self.source_hash} "
            f"pipeline={self.pipeline_version} projection={self.projection_version}"
        )


@dataclass(frozen=True, slots=True)
class ProjectionSkip:
    episode_id: str
    status: ProjectionStatus
    reason: str


@dataclass(frozen=True, slots=True)
class ProjectionAudit:
    projected: int = 0
    duplicate: int = 0
    skipped: int = 0
    rejected: int = 0
    failed: int = 0
    dry_run: bool = False

    def as_dict(self) -> dict[str, int | bool]:
        return {
            "projected": self.projected,
            "duplicate": self.duplicate,
            "skipped": self.skipped,
            "rejected": self.rejected,
            "failed": self.failed,
            "dry_run": self.dry_run,
        }

    def count(self, status: ProjectionStatus) -> ProjectionAudit:
        return replace(self, **{status.value: getattr(self, status.value) + 1})


class ProjectionSink(Protocol):
    def project(self, payload: EpisodeProjectionPayload) -> str: ...


class ProjectionLedger(Protocol):
    def is_projected(self, projection_key: str) -> bool: ...

    def mark_projected(
        self, payload: EpisodeProjectionPayload, graph_ref: str
    ) -> None: ...

    def record_failure(self, payload: EpisodeProjectionPayload, error: str) -> None: ...


def _render_body(
    utterances: tuple[Utterance, ...], facts: tuple[ProjectionFact, ...]
) -> str:
    lines = [u.text.strip() for u in utterances]
    if facts:
        lines.append("")
        lines.append("Accepted claims:")
        lines.extend(f"- [{f.claim_id}] {f.claim_type}: {f.value}" for f in facts)
    return "\n".join(lines)


def build_episode_payload(
    candidate: EpisodeCandidate,
    *,
    projection_version: str,
    min_text_chars: int = DEFAULT_MIN_TEXT_CHARS,
) -> EpisodeProjectionPayload | ProjectionSkip:
    episode = candidate.episode
    if not candidate.utterances:
        return ProjectionSkip(episode.id, ProjectionStatus.REJECTED, "no_evidence")
    if any(u.episode_id != episode.id for u in candidate.utterances):
        return ProjectionSkip(
            episode.id, ProjectionStatus.REJECTED, "utterance_outside_episode"
        )
    accepted = tuple(c for c in candidate.claims if c.status is MemoryStatus.ACCEPTED)
    if any(r.episode_id != episode.id for c in accepted for r in c.evidence):
        return ProjectionSkip(
            episode.id, ProjectionStatus.REJECTED, "claim_evidence_outside_episode"
        )
    text_chars = sum(len("".join(u.text.split())) for u in candidate.utterances)
    if text_chars < min_text_chars:
        return ProjectionSkip(episode.id, ProjectionStatus.SKIPPED, "low_information")

    facts = tuple(
        ProjectionFact(
            claim_id=c.id,
            claim_type=c.claim_type,
            value=c.value,
            valid_from=c.valid_from,
            valid_to=c.valid_to,
            confidence=c.confidence,
            evidence=c.evidence,
        )
        for c in sorted(accepted, key=lambda c: c.id)
    )
    evidence = tuple(dict.fromkeys(ref for fact in facts for ref in fact.evidence))
    return EpisodeProjectionPayload(
        episode_id=episode.id,
        reference_time=episode.started_at,
        body=_render_body(candidate.utterances, facts),
        facts=facts,
        evidence=evidence,
        source_hash=candidate.source_hash,
        pipeline_version=candidate.pipeline_version,
        projection_version=projection_version,
    )


def run_projection(
    candidates: Iterable[EpisodeCandidate],
    sink: ProjectionSink,
    ledger: ProjectionLedger,
    *,
    projection_version: str,
    dry_run: bool = False,
    min_text_chars: int = DEFAULT_MIN_TEXT_CHARS,
) -> ProjectionAudit:
    """Project candidates; sink failures never escape and are retried by re-running."""
    audit = ProjectionAudit(dry_run=dry_run)
    ordered = sorted(candidates, key=lambda c: (c.episode.started_at, c.episode.id))
    for candidate in ordered:
        built = build_episode_payload(
            candidate,
            projection_version=projection_version,
            min_text_chars=min_text_chars,
        )
        if isinstance(built, ProjectionSkip):
            audit = audit.count(built.status)
            continue
        if ledger.is_projected(built.projection_key):
            audit = audit.count(ProjectionStatus.DUPLICATE)
            continue
        if dry_run:
            audit = audit.count(ProjectionStatus.PROJECTED)
            continue
        try:
            graph_ref = sink.project(built)
        except Exception as exc:
            ledger.record_failure(built, f"{type(exc).__name__}: {exc}")
            audit = audit.count(ProjectionStatus.FAILED)
            continue
        ledger.mark_projected(built, graph_ref)
        audit = audit.count(ProjectionStatus.PROJECTED)
    return audit
