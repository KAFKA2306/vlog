from __future__ import annotations

import json
import sys
from dataclasses import asdict, replace
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "packages" / "memory-domain" / "src"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "privacy" / "src"))

from vlog_memory_domain import (  # noqa: E402
    EmotionOrigin,
    EvidenceRef,
    IdentityState,
    InteractionUtteranceValue,
    MemoryClaim,
    MemoryStatus,
    RelationshipValue,
    ResponseKind,
    ResponseValue,
    SelfEmotionValue,
    TimelineEntryKind,
    Utterance,
    deterministic_claim_id,
    ingest_claims,
    retrieve_person_timeline,
    revise_relationship,
    validate_interaction_claim,
)
from vlog_privacy import (  # noqa: E402
    InteractionPublicationDecision,
    project_interaction_claim,
)

FIXTURE = json.loads(
    (REPO_ROOT / "tests" / "fixtures" / "human_memory_interaction.json").read_text(
        encoding="utf-8"
    )
)
SELF = FIXTURE["entities"]["self"]
FRIEND = FIXTURE["entities"]["friend"]
SOURCE = FIXTURE["source_object_id"]
EPISODE = FIXTURE["episode_id"]
U_EMOTION, U_ASK, U_REPLY, U_LATER = (u["id"] for u in FIXTURE["utterances"])
UTTERANCES = {
    u["id"]: Utterance(
        id=u["id"],
        episode_id=EPISODE,
        started_at=datetime.fromisoformat(u["at"]),
        ended_at=datetime.fromisoformat(u["at"]),
        text=u["text"],
        speaker_entity_id=FIXTURE["entities"][u["speaker"]],
    )
    for u in FIXTURE["utterances"]
}
SPANS = {u["id"]: (u["start_ms"], u["end_ms"]) for u in FIXTURE["utterances"]}
AT = {u["id"]: datetime.fromisoformat(u["at"]) for u in FIXTURE["utterances"]}


def ref(utterance_id: str) -> EvidenceRef:
    start, end = SPANS[utterance_id]
    return EvidenceRef(
        source_object_id=SOURCE,
        episode_id=EPISODE,
        utterance_id=utterance_id,
        start_ms=start,
        end_ms=end,
    )


def claim(
    claim_type: str,
    subject: str,
    value: object,
    utterance_id: str,
    status: MemoryStatus = MemoryStatus.ACCEPTED,
) -> MemoryClaim:
    evidence = (ref(utterance_id),)
    return MemoryClaim(
        id=deterministic_claim_id(claim_type, subject, evidence, value),
        claim_type=claim_type,
        subject_entity_id=subject,
        value=value,
        valid_from=AT[utterance_id],
        evidence=evidence,
        status=status,
    )


def emotion() -> MemoryClaim:
    return claim(
        "self_emotion",
        SELF,
        SelfEmotionValue(origin=EmotionOrigin.SELF_EXPLICIT, label="nervous"),
        U_EMOTION,
    )


def ask() -> MemoryClaim:
    return claim(
        "interaction_utterance",
        SELF,
        InteractionUtteranceValue(
            speaker_state=IdentityState.CONFIRMED,
            speaker_entity_id=SELF,
            target_state=IdentityState.CONFIRMED,
            target_entity_id=FRIEND,
        ),
        U_ASK,
    )


def reply() -> MemoryClaim:
    return claim(
        "interaction_response",
        FRIEND,
        ResponseValue(
            kind=ResponseKind.SPOKEN,
            responder_entity_id=FRIEND,
            in_reply_to_claim_id=ask().id,
        ),
        U_REPLY,
    )


def relationship(label: str, utterance_id: str) -> MemoryClaim:
    return claim(
        "relationship",
        SELF,
        RelationshipValue(other_entity_id=FRIEND, relation=label),
        utterance_id,
    )


def scenario() -> tuple[tuple[MemoryClaim, ...], tuple]:
    first = relationship("collaborator", U_REPLY)
    second = relationship("close_collaborator", U_LATER)
    new_claim, revision = revise_relationship(
        first,
        second,
        revised_at=AT[U_LATER],
        reason="friend asked to work together",
    )
    claims = (emotion(), ask(), reply(), first, new_claim)
    return claims, (revision,)


def test_end_to_end_chain_regenerates_in_time_order() -> None:
    claims, revisions = scenario()
    for c in claims:
        validate_interaction_claim(c, utterances_by_id=UTTERANCES)
    timeline = retrieve_person_timeline(claims, revisions, FRIEND)
    assert [e.kind for e in timeline] == [
        TimelineEntryKind.INTERACTION,
        TimelineEntryKind.RESPONSE,
        TimelineEntryKind.RELATIONSHIP,
        TimelineEntryKind.RELATIONSHIP_REVISION,
        TimelineEntryKind.RELATIONSHIP,
    ]
    assert [e.at for e in timeline] == sorted(e.at for e in timeline)
    own = retrieve_person_timeline(claims, revisions, SELF)
    assert TimelineEntryKind.SELF_EMOTION in {e.kind for e in own}


def test_accepted_claims_trace_to_source_span() -> None:
    claims, _ = scenario()
    for c in claims:
        assert c.evidence[0].source_object_id == SOURCE
        assert c.evidence[0].start_ms is not None
        assert c.evidence[0].utterance_id in UTTERANCES


def test_ai_inferred_emotion_cannot_be_accepted_or_confused() -> None:
    inferred = SelfEmotionValue(origin=EmotionOrigin.AI_INFERRED, label="anxious")
    with pytest.raises(ValueError, match="AI-inferred"):
        validate_interaction_claim(
            claim("self_emotion", SELF, inferred, U_EMOTION),
            utterances_by_id=UTTERANCES,
        )
    candidate = claim(
        "self_emotion", SELF, inferred, U_EMOTION, status=MemoryStatus.CANDIDATE
    )
    validate_interaction_claim(candidate, utterances_by_id=UTTERANCES)
    assert candidate.value.origin is not emotion().value.origin


def test_explicit_emotion_must_come_from_self_utterance() -> None:
    wrong = claim(
        "self_emotion",
        SELF,
        SelfEmotionValue(origin=EmotionOrigin.SELF_EXPLICIT, label="nervous"),
        U_REPLY,
    )
    with pytest.raises(ValueError, match="self"):
        validate_interaction_claim(wrong, utterances_by_id=UTTERANCES)


def test_inner_state_of_other_cannot_be_accepted() -> None:
    inferred = ResponseValue(
        kind=ResponseKind.INFERRED_INNER_STATE,
        responder_entity_id=FRIEND,
        in_reply_to_claim_id=ask().id,
    )
    with pytest.raises(ValueError, match="inner state"):
        validate_interaction_claim(
            claim("interaction_response", FRIEND, inferred, U_REPLY),
            utterances_by_id=UTTERANCES,
        )
    with pytest.raises(ValueError, match="require provenance"):
        MemoryClaim(
            claim_type="interaction_response",
            subject_entity_id=FRIEND,
            value=inferred,
            valid_from=AT[U_REPLY],
            evidence=(),
            status=MemoryStatus.ACCEPTED,
        )
    candidate = claim(
        "interaction_response",
        FRIEND,
        inferred,
        U_REPLY,
        status=MemoryStatus.CANDIDATE,
    )
    validate_interaction_claim(candidate, utterances_by_id=UTTERANCES)


def test_spoken_response_requires_raw_utterance_by_responder() -> None:
    spoken_by_self = claim(
        "interaction_response",
        FRIEND,
        ResponseValue(
            kind=ResponseKind.SPOKEN,
            responder_entity_id=FRIEND,
            in_reply_to_claim_id=ask().id,
        ),
        U_ASK,
    )
    with pytest.raises(ValueError, match="responder"):
        validate_interaction_claim(spoken_by_self, utterances_by_id=UTTERANCES)
    with pytest.raises(ValueError, match="raw utterance"):
        validate_interaction_claim(reply(), utterances_by_id={})


def test_uncertain_identity_never_falls_back_to_a_confirmed_value() -> None:
    with pytest.raises(ValueError, match="confirmed"):
        InteractionUtteranceValue(
            speaker_state=IdentityState.UNKNOWN,
            speaker_entity_id=FRIEND,
            target_state=IdentityState.CONFIRMED,
            target_entity_id=SELF,
        )
    with pytest.raises(ValueError, match="entity id"):
        InteractionUtteranceValue(
            speaker_state=IdentityState.CONFIRMED,
            speaker_entity_id=None,
            target_state=IdentityState.UNKNOWN,
        )
    uncertain = InteractionUtteranceValue(
        speaker_state=IdentityState.UNCERTAIN,
        speaker_entity_id=None,
        target_state=IdentityState.UNKNOWN,
        speaker_confidence=0.4,
    )
    assert uncertain.speaker_entity_id is None
    assert uncertain.target_entity_id is None


def test_confirmed_speaker_must_match_raw_utterance_speaker() -> None:
    mismatch = claim(
        "interaction_utterance",
        SELF,
        InteractionUtteranceValue(
            speaker_state=IdentityState.CONFIRMED,
            speaker_entity_id=FRIEND,
            target_state=IdentityState.UNKNOWN,
        ),
        U_ASK,
    )
    with pytest.raises(ValueError, match="speaker"):
        validate_interaction_claim(mismatch, utterances_by_id=UTTERANCES)


def test_relationship_revision_is_append_only() -> None:
    first = relationship("collaborator", U_REPLY)
    snapshot = asdict(first)
    second = relationship("close_collaborator", U_LATER)
    new_claim, revision = revise_relationship(
        first, second, revised_at=AT[U_LATER], reason="asked to work together"
    )
    assert asdict(first) == snapshot
    assert revision.claim_id == first.id
    assert revision.previous_status is MemoryStatus.ACCEPTED
    assert revision.new_status is MemoryStatus.SUPERSEDED
    assert new_claim.value.supersedes_claim_id == first.id
    assert new_claim.id != first.id


def test_revision_requires_new_evidence_and_same_pair() -> None:
    first = relationship("collaborator", U_REPLY)
    no_evidence = replace(
        relationship("close_collaborator", U_LATER),
        status=MemoryStatus.CANDIDATE,
        evidence=(),
    )
    with pytest.raises(ValueError, match="evidence"):
        revise_relationship(first, no_evidence, revised_at=AT[U_LATER], reason="x")
    other = claim(
        "relationship",
        SELF,
        RelationshipValue(other_entity_id=str(uuid4()), relation="x"),
        U_LATER,
    )
    with pytest.raises(ValueError, match="same"):
        revise_relationship(first, other, revised_at=AT[U_LATER], reason="x")


def test_reingest_same_evidence_does_not_duplicate() -> None:
    claims, _ = scenario()
    once = ingest_claims((), claims)
    twice = ingest_claims(once, claims)
    assert twice == once
    assert len({c.id for c in twice}) == len(claims)


def test_reingest_conflicting_content_under_same_id_is_rejected() -> None:
    original = emotion()
    tampered = replace(original, confidence=0.99)
    with pytest.raises(ValueError, match="conflict"):
        ingest_claims((original,), (tampered,))


def test_private_interaction_is_not_public_without_decision() -> None:
    claims, _ = scenario()
    for c in claims:
        decision = InteractionPublicationDecision(
            claim_id=c.id,
            decided_at=AT[U_LATER],
            decided_by="owner",
            rationale="default private",
        )
        assert project_interaction_claim(c, decision) is None


def test_approved_projection_hides_people_and_evidence() -> None:
    c = ask()
    decision = InteractionPublicationDecision(
        claim_id=c.id,
        decided_at=AT[U_LATER],
        decided_by="owner",
        rationale="approved synthetic",
        publish=True,
    )
    projection = project_interaction_claim(c, decision)
    assert projection is not None
    dumped = json.dumps(asdict(projection), default=str)
    for secret in (SELF, FRIEND, SOURCE, EPISODE, U_ASK):
        assert secret not in dumped
    with pytest.raises(ValueError, match="reference"):
        project_interaction_claim(emotion(), decision)
    candidate = replace(c, status=MemoryStatus.CANDIDATE)
    with pytest.raises(ValueError, match="accepted"):
        project_interaction_claim(candidate, decision)


def test_timeline_includes_open_loops_for_person() -> None:
    open_loop = claim(
        "open_loop",
        SELF,
        {"entity_id": FRIEND, "task": "send draft"},
        U_ASK,
    )
    entries = retrieve_person_timeline((open_loop,), (), FRIEND)
    assert [e.kind for e in entries] == [TimelineEntryKind.OPEN_LOOP]
    closed = replace(open_loop, valid_to=AT[U_REPLY])
    assert retrieve_person_timeline((closed,), (), FRIEND) == ()
