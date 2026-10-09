from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "packages" / "memory-domain" / "src"))

from vlog_memory_domain import (  # noqa: E402
    EvidenceRef,
    MemoryClaim,
    SocialMirrorEvidenceLevel,
    SocialMirrorValue,
    Utterance,
    validate_social_mirror_claim,
)

NOW = datetime(2026, 8, 13, 10, 0, tzinfo=timezone.utc)


def make_evidence(*, episode_id: str, utterance_id: str | None = None) -> EvidenceRef:
    return EvidenceRef(
        source_object_id=str(uuid4()),
        episode_id=episode_id,
        utterance_id=utterance_id,
    )


def make_claim(
    value: SocialMirrorValue, evidence: tuple[EvidenceRef, ...]
) -> MemoryClaim:
    return MemoryClaim(
        claim_type="social_mirror",
        subject_entity_id=str(uuid4()),
        value=value,
        valid_from=NOW,
        evidence=evidence,
    )


def test_direct_quote_requires_verbatim_raw_utterance_match() -> None:
    episode_id = str(uuid4())
    utterance_id = str(uuid4())
    evidence = make_evidence(episode_id=episode_id, utterance_id=utterance_id)
    claim = make_claim(
        SocialMirrorValue(
            evidence_level=SocialMirrorEvidenceLevel.DIRECT_QUOTE,
            text="研究しすぎ",
            speaker_label="friend-a",
        ),
        (evidence,),
    )
    utterance = Utterance(
        id=utterance_id,
        episode_id=episode_id,
        started_at=NOW,
        ended_at=NOW + timedelta(seconds=2),
        text="いや、研究しすぎでしょ",
    )

    validate_social_mirror_claim(claim, utterances_by_id={utterance_id: utterance})


def test_summary_quote_cannot_promote_without_raw_utterance_evidence() -> None:
    episode_id = str(uuid4())
    claim = make_claim(
        SocialMirrorValue(
            evidence_level=SocialMirrorEvidenceLevel.DIRECT_QUOTE,
            text="魔王が来た",
            speaker_label="unknown",
        ),
        (make_evidence(episode_id=episode_id),),
    )

    with pytest.raises(ValueError, match="referenced raw utterance"):
        validate_social_mirror_claim(claim, utterances_by_id={})


def test_direct_quote_rejects_text_that_is_not_verbatim() -> None:
    episode_id = str(uuid4())
    utterance_id = str(uuid4())
    evidence = make_evidence(episode_id=episode_id, utterance_id=utterance_id)
    claim = make_claim(
        SocialMirrorValue(
            evidence_level=SocialMirrorEvidenceLevel.DIRECT_QUOTE,
            text="とても詳しい",
            speaker_label="friend-b",
        ),
        (evidence,),
    )
    utterance = Utterance(
        id=utterance_id,
        episode_id=episode_id,
        started_at=NOW,
        ended_at=NOW + timedelta(seconds=1),
        text="詳しすぎる",
    )

    with pytest.raises(ValueError, match="appear verbatim"):
        validate_social_mirror_claim(claim, utterances_by_id={utterance_id: utterance})


def test_paraphrase_is_evidence_backed_but_not_verbatim() -> None:
    episode_id = str(uuid4())
    value = SocialMirrorValue(
        evidence_level=SocialMirrorEvidenceLevel.PARAPHRASE,
        text="かなり詳しい人だと言われた",
        speaker_label="friend-c",
    )
    claim = make_claim(value, (make_evidence(episode_id=episode_id),))

    validate_social_mirror_claim(claim)

    assert value.is_spoken_fact is True
    assert value.is_verbatim is False


def test_inferred_impression_is_never_a_spoken_fact() -> None:
    episode_id = str(uuid4())
    value = SocialMirrorValue(
        evidence_level=SocialMirrorEvidenceLevel.INFERRED_IMPRESSION,
        text="相手は圧倒されたように見えた",
        speaker_label="unknown",
    )
    claim = make_claim(value, (make_evidence(episode_id=episode_id),))

    validate_social_mirror_claim(claim)

    assert value.is_spoken_fact is False
    assert value.is_verbatim is False


def test_unknown_speaker_remains_unknown_without_identity_guessing() -> None:
    value = SocialMirrorValue(
        evidence_level=SocialMirrorEvidenceLevel.PARAPHRASE,
        text="詳しすぎると言われた",
        speaker_label="unknown",
    )

    assert value.speaker_label == "unknown"
    assert value.speaker_entity_id is None


def test_social_mirror_schema_fixes_evidence_levels_and_required_metadata() -> None:
    schema = json.loads(
        (REPO_ROOT / "schemas" / "memory-claim.schema.json").read_text()
    )
    value_schema = schema["$defs"]["socialMirrorValue"]

    assert set(value_schema["required"]) == {
        "evidence_level",
        "text",
        "speaker_label",
    }
    assert value_schema["properties"]["evidence_level"]["enum"] == [
        "direct_quote",
        "paraphrase",
        "inferred_impression",
    ]

    social_mirror_rule = schema["allOf"][1]
    assert (
        social_mirror_rule["if"]["properties"]["claim_type"]["const"] == "social_mirror"
    )
    assert social_mirror_rule["then"]["properties"]["evidence"]["minItems"] == 1
