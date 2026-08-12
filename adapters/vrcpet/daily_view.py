from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from numbers import Real
from typing import Iterable, Mapping, Sequence

from .normalizer import NormalizedObservation
from .snapshot import (
    ProfileDiff,
    StateSnapshot,
    VocabularyDiff,
    extract_vocabulary_counts,
)


@dataclass(frozen=True, slots=True)
class CompanionDailyView:
    day: date
    conversation_records: int
    operational_records: int
    parse_issues: int
    snapshots: int
    frequent_terms: tuple[tuple[str, Real], ...]
    newly_learned_terms: tuple[str, ...]
    strengthened_terms: tuple[str, ...]
    weakened_or_missing_terms: tuple[str, ...]
    pet_utterances: tuple[str, ...]
    profile_changes: tuple[str, ...]

    def render_markdown(self, *, pet_name: str = "すい") -> str:
        def joined(values: Sequence[str]) -> str:
            return "、".join(values) if values else "なし"

        frequent = (
            "、".join(f"{term}({count})" for term, count in self.frequent_terms)
            if self.frequent_terms
            else "なし"
        )
        return "\n".join(
            (
                f"# {pet_name}の目から見た{self.day.isoformat()}",
                "",
                f"- 会話観測: {self.conversation_records}件",
                f"- operational observation: {self.operational_records}件",
                f"- state snapshot: {self.snapshots}件",
                f"- parse isolation/audit: {self.parse_issues}件",
                f"- よく聞いた言葉: {frequent}",
                f"- 新しく覚えた言葉: {joined(self.newly_learned_terms)}",
                f"- 強くなった言葉: {joined(self.strengthened_terms)}",
                f"- 弱くなった/消えた言葉: {joined(self.weakened_or_missing_terms)}",
                f"- ムチォ側の発話: {joined(self.pet_utterances)}",
                f"- profile変化: {joined(self.profile_changes)}",
            )
        )


def _counts_from_observations(
    observations: tuple[NormalizedObservation, ...],
) -> Mapping[str, Real]:
    for observation in observations:
        if observation.parsed.observation_type != "vocabulary":
            continue
        if not observation.parsed.records:
            continue
        return extract_vocabulary_counts(observation.parsed.records[0])
    return {}


def build_companion_daily_view(
    *,
    day: date,
    observations: Iterable[NormalizedObservation],
    snapshots: Iterable[StateSnapshot] = (),
    current_counts: Mapping[str, Real] | None = None,
    vocabulary_diff: VocabularyDiff | None = None,
    profile_diff: ProfileDiff | None = None,
    pet_utterances: Sequence[str] = (),
) -> CompanionDailyView:
    observed = tuple(observations)
    snapshot_items = tuple(snapshots)
    conversation_records = sum(
        len(item.parsed.records)
        for item in observed
        if item.parsed.observation_type == "conversation"
    )
    operational_records = sum(
        len(item.parsed.records)
        for item in observed
        if item.parsed.observation_type == "operational"
    )
    parse_issues = sum(len(item.parsed.issues) for item in observed)

    counts = current_counts if current_counts is not None else _counts_from_observations(observed)
    frequent_terms = tuple(
        sorted(
            (
                (key, value)
                for key, value in counts.items()
                if isinstance(value, Real) and not isinstance(value, bool)
            ),
            key=lambda item: (-item[1], item[0]),
        )[:10]
    )
    if vocabulary_diff is None:
        new_terms: tuple[str, ...] = ()
        strengthened_terms: tuple[str, ...] = ()
        weakened_terms: tuple[str, ...] = ()
    else:
        new_terms = tuple(sorted(vocabulary_diff.new))
        strengthened_terms = tuple(sorted(vocabulary_diff.increased))
        weakened_terms = tuple(
            sorted(set(vocabulary_diff.decreased) | set(vocabulary_diff.missing))
        )

    if profile_diff is None:
        profile_changes: tuple[str, ...] = ()
    else:
        profile_changes = tuple(
            sorted(
                set(profile_diff.added)
                | set(profile_diff.removed)
                | set(profile_diff.changed)
            )
        )

    return CompanionDailyView(
        day=day,
        conversation_records=conversation_records,
        operational_records=operational_records,
        parse_issues=parse_issues,
        snapshots=len(snapshot_items),
        frequent_terms=frequent_terms,
        newly_learned_terms=new_terms,
        strengthened_terms=strengthened_terms,
        weakened_or_missing_terms=weakened_terms,
        pet_utterances=tuple(pet_utterances),
        profile_changes=profile_changes,
    )
