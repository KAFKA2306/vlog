from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from numbers import Real
from typing import Any, Mapping

from .normalizer import NormalizedObservation


@dataclass(frozen=True, slots=True)
class StateSnapshot:
    captured_on: date
    observation_type: str
    source_object_id: str
    sha256: str
    object_uri: str
    raw_bytes: bytes

    @property
    def idempotency_key(self) -> str:
        return f"{self.captured_on.isoformat()}:{self.observation_type}:{self.sha256}"


@dataclass(frozen=True, slots=True)
class VocabularyDiff:
    new: Mapping[str, Real]
    increased: Mapping[str, tuple[Real, Real]]
    decreased: Mapping[str, tuple[Real, Real]]
    missing: Mapping[str, Real]


@dataclass(frozen=True, slots=True)
class ProfileDiff:
    added: Mapping[str, Any]
    removed: Mapping[str, Any]
    changed: Mapping[str, tuple[Any, Any]]


def build_state_snapshot(
    observation: NormalizedObservation,
    *,
    captured_on: date,
) -> StateSnapshot:
    observation_type = observation.parsed.observation_type
    if observation_type not in {"profile", "vocabulary"}:
        raise ValueError("only profile/vocabulary observations are state snapshots")
    return StateSnapshot(
        captured_on=captured_on,
        observation_type=observation_type,
        source_object_id=observation.source_object.id,
        sha256=observation.source_hash,
        object_uri=(
            "private://vrcpet/snapshots/"
            f"{captured_on.isoformat()}/{observation_type}/"
            f"{observation.source_hash}"
        ),
        raw_bytes=observation.raw_bytes,
    )


def diff_vocabulary_counts(
    previous: Mapping[str, Real],
    current: Mapping[str, Real],
) -> VocabularyDiff:
    def numeric_items(values: Mapping[str, Real]) -> dict[str, Real]:
        return {
            key: value
            for key, value in values.items()
            if isinstance(value, Real) and not isinstance(value, bool)
        }

    before = numeric_items(previous)
    after = numeric_items(current)
    new = {key: after[key] for key in after.keys() - before.keys()}
    missing = {key: before[key] for key in before.keys() - after.keys()}
    increased = {
        key: (before[key], after[key])
        for key in before.keys() & after.keys()
        if after[key] > before[key]
    }
    decreased = {
        key: (before[key], after[key])
        for key in before.keys() & after.keys()
        if after[key] < before[key]
    }
    return VocabularyDiff(
        new=new,
        increased=increased,
        decreased=decreased,
        missing=missing,
    )


def diff_profile(
    previous: Mapping[str, Any],
    current: Mapping[str, Any],
) -> ProfileDiff:
    added = {key: current[key] for key in current.keys() - previous.keys()}
    removed = {key: previous[key] for key in previous.keys() - current.keys()}
    changed = {
        key: (previous[key], current[key])
        for key in previous.keys() & current.keys()
        if previous[key] != current[key]
    }
    return ProfileDiff(added=added, removed=removed, changed=changed)
