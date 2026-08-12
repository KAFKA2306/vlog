"""VRCPet/Muchio private observation adapter for Human Memory v2."""

from .daily_view import CompanionDailyView, build_companion_daily_view
from .normalizer import (
    NormalizedObservation,
    associate_episode,
    build_ingestion_run,
    deduplicate_observations,
    normalize_source,
)
from .parser import ParseIssue, ParsedObservation, parse_observation
from .reader import (
    SourceBoundaryError,
    SourceFile,
    UnstableSourceError,
    discover_source_paths,
    read_source_file,
    validate_source_root,
)
from .snapshot import (
    ProfileDiff,
    StateSnapshot,
    VocabularyDiff,
    build_state_snapshot,
    diff_profile,
    diff_vocabulary_counts,
)

__all__ = [
    "CompanionDailyView",
    "NormalizedObservation",
    "ParseIssue",
    "ParsedObservation",
    "ProfileDiff",
    "SourceBoundaryError",
    "SourceFile",
    "StateSnapshot",
    "UnstableSourceError",
    "VocabularyDiff",
    "associate_episode",
    "build_companion_daily_view",
    "build_ingestion_run",
    "build_state_snapshot",
    "deduplicate_observations",
    "diff_profile",
    "diff_vocabulary_counts",
    "discover_source_paths",
    "normalize_source",
    "parse_observation",
    "read_source_file",
    "validate_source_root",
]
