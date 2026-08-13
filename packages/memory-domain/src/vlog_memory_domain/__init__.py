"""Canonical Human Memory Repository v2 domain model.

This package contains storage-agnostic entities only. Persistence, retrieval,
AI extraction, and publication are adapter concerns.
"""

from .models import (
    Artifact,
    ArtifactKind,
    Entity,
    Episode,
    EvidenceRef,
    IngestionRun,
    IngestionStatus,
    MemoryClaim,
    MemoryRevision,
    MemoryStatus,
    Moment,
    PrivacyLevel,
    PublicationDecision,
    SourceKind,
    SourceObject,
    Utterance,
)
from .social_mirror import (
    SOCIAL_MIRROR_CLAIM_TYPE,
    UNKNOWN_SPEAKER,
    SocialMirrorEvidenceLevel,
    SocialMirrorValue,
    validate_social_mirror_claim,
)

__all__ = [
    "Artifact",
    "ArtifactKind",
    "Entity",
    "Episode",
    "EvidenceRef",
    "IngestionRun",
    "IngestionStatus",
    "MemoryClaim",
    "MemoryRevision",
    "MemoryStatus",
    "Moment",
    "PrivacyLevel",
    "PublicationDecision",
    "SOCIAL_MIRROR_CLAIM_TYPE",
    "SourceKind",
    "SourceObject",
    "SocialMirrorEvidenceLevel",
    "SocialMirrorValue",
    "UNKNOWN_SPEAKER",
    "Utterance",
    "validate_social_mirror_claim",
]
