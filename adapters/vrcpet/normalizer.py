from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Iterable, Mapping
from uuid import UUID, uuid5

from vlog_memory_domain import (
    Episode,
    IngestionRun,
    IngestionStatus,
    PrivacyLevel,
    SourceKind,
    SourceObject,
)

from .parser import ParsedObservation
from .reader import SourceFile

VRC_PET_NAMESPACE = UUID("7b042afa-2563-5c4f-81c5-f35fd0f7c7cc")


@dataclass(frozen=True, slots=True)
class NormalizedObservation:
    source_object: SourceObject
    manifest: Mapping[str, Any]
    parsed: ParsedObservation
    raw_bytes: bytes

    @property
    def source_hash(self) -> str:
        return self.source_object.sha256


def _source_kind(observation_type: str) -> SourceKind:
    if observation_type == "conversation":
        return SourceKind.CONVERSATION
    return SourceKind.DOCUMENT


def normalize_source(
    source: SourceFile,
    parsed: ParsedObservation,
) -> NormalizedObservation:
    digest = sha256(source.raw_bytes).hexdigest()
    kind = _source_kind(parsed.observation_type)
    source_id = str(uuid5(VRC_PET_NAMESPACE, f"{parsed.observation_type}:{digest}"))
    recorded_at = datetime.fromtimestamp(source.mtime_ns / 1_000_000_000, timezone.utc)
    object_uri = f"private://vrcpet/{parsed.observation_type}/sha256/{digest}"

    source_object = SourceObject(
        id=source_id,
        kind=kind,
        object_uri=object_uri,
        sha256=digest,
        size_bytes=source.size_bytes,
        recorded_at=recorded_at,
        privacy=PrivacyLevel.PRIVATE,
    )
    manifest = {
        "id": source_object.id,
        "kind": source_object.kind.value,
        "object_uri": source_object.object_uri,
        "sha256": source_object.sha256,
        "size_bytes": source_object.size_bytes,
        "recorded_at": source_object.recorded_at.isoformat(),
        "privacy": source_object.privacy.value,
        "original_filename": source.relative_path.rsplit("/", 1)[-1],
        "metadata": {
            "source": "vrcpet",
            "observation_type": parsed.observation_type,
            "source_relative_path": source.relative_path,
            "source_mtime_ns": source.mtime_ns,
            "parse_issue_count": len(parsed.issues),
        },
    }
    return NormalizedObservation(
        source_object=source_object,
        manifest=manifest,
        parsed=parsed,
        raw_bytes=source.raw_bytes,
    )


def deduplicate_observations(
    observations: Iterable[NormalizedObservation],
) -> tuple[NormalizedObservation, ...]:
    by_id: dict[str, NormalizedObservation] = {}
    for observation in observations:
        by_id.setdefault(observation.source_object.id, observation)
    return tuple(by_id.values())


def build_ingestion_run(
    observation: NormalizedObservation,
    *,
    pipeline_version: str,
    at: datetime | None = None,
) -> IngestionRun:
    timestamp = at or datetime.now(timezone.utc)
    return IngestionRun(
        source_hash=observation.source_hash,
        pipeline_version=pipeline_version,
        status=IngestionStatus.SUCCEEDED,
        started_at=timestamp,
        completed_at=timestamp,
    )


def associate_episode(
    episode: Episode,
    observations: Iterable[NormalizedObservation],
) -> Episode:
    source_ids = list(episode.source_object_ids)
    for observation in observations:
        source_id = observation.source_object.id
        if source_id not in source_ids:
            source_ids.append(source_id)
    return Episode(
        id=episode.id,
        started_at=episode.started_at,
        ended_at=episode.ended_at,
        source_object_ids=tuple(source_ids),
        title=episode.title,
    )
