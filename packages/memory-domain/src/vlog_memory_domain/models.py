from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any, Mapping
from uuid import UUID, uuid4


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


def _validate_sha256(value: str, field_name: str) -> None:
    if len(value) != 64 or any(
        ch not in "0123456789abcdef" for ch in value.lower()
    ):
        raise ValueError(f"{field_name} must be a 64-character hexadecimal digest")


def _is_machine_local_locator(value: str) -> bool:
    lowered = value.lower()
    return (
        PureWindowsPath(value).is_absolute()
        or PurePosixPath(value).is_absolute()
        or lowered.startswith("file:")
    )


def _validate_object_uri(value: str, privacy: PrivacyLevel) -> None:
    if not value.strip():
        raise ValueError("object_uri must not be empty")
    if _is_machine_local_locator(value):
        raise ValueError("object_uri must not be a machine-local filesystem path")
    if not value.startswith("private://") and privacy is not PrivacyLevel.PUBLIC:
        raise ValueError("non-public source objects must use a private:// object URI")


class PrivacyLevel(StrEnum):
    PRIVATE = "private"
    SENSITIVE = "sensitive"
    INTERNAL = "internal"
    PUBLIC = "public"


class SourceKind(StrEnum):
    AUDIO = "audio"
    PHOTO = "photo"
    VIDEO = "video"
    TRANSCRIPT = "transcript"
    CONVERSATION = "conversation"
    DOCUMENT = "document"


class MemoryStatus(StrEnum):
    CANDIDATE = "candidate"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    FORGOTTEN = "forgotten"


class IngestionStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ArtifactKind(StrEnum):
    DIARY = "diary"
    NOVEL = "novel"
    ILLUSTRATION = "illustration"
    MONTHLY_REVIEW = "monthly_review"


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    """A precise, immutable pointer from a memory claim to its evidence."""

    source_object_id: str
    episode_id: str
    utterance_id: str | None = None
    start_ms: int | None = None
    end_ms: int | None = None

    def __post_init__(self) -> None:
        _validate_id(self.source_object_id, "source_object_id")
        _validate_id(self.episode_id, "episode_id")
        if self.utterance_id is not None:
            _validate_id(self.utterance_id, "utterance_id")
        if (self.start_ms is None) != (self.end_ms is None):
            raise ValueError("start_ms and end_ms must be provided together")
        if self.start_ms is not None:
            if self.start_ms < 0 or self.end_ms is None or self.end_ms < self.start_ms:
                raise ValueError("evidence time range is invalid")


@dataclass(frozen=True, slots=True)
class SourceObject:
    kind: SourceKind
    object_uri: str
    sha256: str
    size_bytes: int
    recorded_at: datetime
    privacy: PrivacyLevel = PrivacyLevel.PRIVATE
    id: str = field(default_factory=_new_id)

    def __post_init__(self) -> None:
        _validate_id(self.id, "id")
        _validate_aware(self.recorded_at, "recorded_at")
        _validate_object_uri(self.object_uri, self.privacy)
        _validate_sha256(self.sha256, "sha256")
        if self.size_bytes < 0:
            raise ValueError("size_bytes must not be negative")


@dataclass(frozen=True, slots=True)
class Episode:
    started_at: datetime
    ended_at: datetime
    source_object_ids: tuple[str, ...]
    title: str | None = None
    id: str = field(default_factory=_new_id)

    def __post_init__(self) -> None:
        _validate_id(self.id, "id")
        _validate_aware(self.started_at, "started_at")
        _validate_aware(self.ended_at, "ended_at")
        if self.ended_at < self.started_at:
            raise ValueError("ended_at must not precede started_at")
        if not self.source_object_ids:
            raise ValueError("an episode must reference at least one source object")
        for source_id in self.source_object_ids:
            _validate_id(source_id, "source_object_ids")


@dataclass(frozen=True, slots=True)
class Utterance:
    episode_id: str
    started_at: datetime
    ended_at: datetime
    text: str
    speaker_entity_id: str | None = None
    id: str = field(default_factory=_new_id)

    def __post_init__(self) -> None:
        _validate_id(self.id, "id")
        _validate_id(self.episode_id, "episode_id")
        if self.speaker_entity_id is not None:
            _validate_id(self.speaker_entity_id, "speaker_entity_id")
        _validate_aware(self.started_at, "started_at")
        _validate_aware(self.ended_at, "ended_at")
        if self.ended_at < self.started_at:
            raise ValueError("ended_at must not precede started_at")
        if not self.text.strip():
            raise ValueError("utterance text must not be empty")


@dataclass(frozen=True, slots=True)
class Moment:
    episode_id: str
    summary: str
    evidence: tuple[EvidenceRef, ...]
    importance: float = 0.5
    id: str = field(default_factory=_new_id)

    def __post_init__(self) -> None:
        _validate_id(self.id, "id")
        _validate_id(self.episode_id, "episode_id")
        if not self.summary.strip():
            raise ValueError("moment summary must not be empty")
        if not self.evidence:
            raise ValueError("a moment must retain evidence")
        if not 0.0 <= self.importance <= 1.0:
            raise ValueError("importance must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class Entity:
    entity_type: str
    canonical_name: str
    aliases: tuple[str, ...] = ()
    attributes: Mapping[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=_new_id)

    def __post_init__(self) -> None:
        _validate_id(self.id, "id")
        if not self.entity_type.strip():
            raise ValueError("entity_type must not be empty")
        if not self.canonical_name.strip():
            raise ValueError("canonical_name must not be empty")


@dataclass(frozen=True, slots=True)
class MemoryClaim:
    claim_type: str
    subject_entity_id: str
    value: Any
    valid_from: datetime
    evidence: tuple[EvidenceRef, ...]
    status: MemoryStatus = MemoryStatus.CANDIDATE
    valid_to: datetime | None = None
    confidence: float = 0.5
    id: str = field(default_factory=_new_id)

    def __post_init__(self) -> None:
        _validate_id(self.id, "id")
        _validate_id(self.subject_entity_id, "subject_entity_id")
        _validate_aware(self.valid_from, "valid_from")
        if self.valid_to is not None:
            _validate_aware(self.valid_to, "valid_to")
            if self.valid_to < self.valid_from:
                raise ValueError("valid_to must not precede valid_from")
        if not self.claim_type.strip():
            raise ValueError("claim_type must not be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.status is MemoryStatus.ACCEPTED and not self.evidence:
            raise ValueError("accepted memory claims require provenance evidence")


@dataclass(frozen=True, slots=True)
class MemoryRevision:
    claim_id: str
    previous_status: MemoryStatus
    new_status: MemoryStatus
    reason: str
    revised_at: datetime
    evidence: tuple[EvidenceRef, ...] = ()
    supersedes_revision_id: str | None = None
    id: str = field(default_factory=_new_id)

    def __post_init__(self) -> None:
        _validate_id(self.id, "id")
        _validate_id(self.claim_id, "claim_id")
        if self.supersedes_revision_id is not None:
            _validate_id(self.supersedes_revision_id, "supersedes_revision_id")
        _validate_aware(self.revised_at, "revised_at")
        if not self.reason.strip():
            raise ValueError("revision reason must not be empty")
        if self.new_status is MemoryStatus.ACCEPTED and not self.evidence:
            raise ValueError("accepting a claim requires provenance evidence")


@dataclass(frozen=True, slots=True)
class Artifact:
    kind: ArtifactKind
    generated_at: datetime
    source_episode_ids: tuple[str, ...]
    source_claim_ids: tuple[str, ...]
    content_uri: str
    generator_version: str
    id: str = field(default_factory=_new_id)

    def __post_init__(self) -> None:
        _validate_id(self.id, "id")
        _validate_aware(self.generated_at, "generated_at")
        if not self.source_episode_ids and not self.source_claim_ids:
            raise ValueError("an artifact must reference canonical memory or evidence")
        for episode_id in self.source_episode_ids:
            _validate_id(episode_id, "source_episode_ids")
        for claim_id in self.source_claim_ids:
            _validate_id(claim_id, "source_claim_ids")
        if not self.content_uri.strip():
            raise ValueError("content_uri must not be empty")
        if not self.generator_version.strip():
            raise ValueError("generator_version must not be empty")


@dataclass(frozen=True, slots=True)
class IngestionRun:
    source_hash: str
    pipeline_version: str
    status: IngestionStatus
    started_at: datetime
    completed_at: datetime | None = None
    error: str | None = None
    id: str = field(default_factory=_new_id)

    def __post_init__(self) -> None:
        _validate_id(self.id, "id")
        _validate_aware(self.started_at, "started_at")
        if self.completed_at is not None:
            _validate_aware(self.completed_at, "completed_at")
            if self.completed_at < self.started_at:
                raise ValueError("completed_at must not precede started_at")
        _validate_sha256(self.source_hash, "source_hash")
        if not self.pipeline_version.strip():
            raise ValueError("pipeline_version is required")
        if self.status is IngestionStatus.FAILED and not self.error:
            raise ValueError("failed ingestion runs require an error")

    @property
    def idempotency_key(self) -> str:
        return f"{self.source_hash}:{self.pipeline_version}"


@dataclass(frozen=True, slots=True)
class PublicationDecision:
    artifact_id: str
    approved: bool
    decided_at: datetime
    decided_by: str
    rationale: str
    id: str = field(default_factory=_new_id)

    def __post_init__(self) -> None:
        _validate_id(self.id, "id")
        _validate_id(self.artifact_id, "artifact_id")
        _validate_aware(self.decided_at, "decided_at")
        if not self.decided_by.strip():
            raise ValueError("decided_by must not be empty")
        if not self.rationale.strip():
            raise ValueError("publication decisions require an explicit rationale")
