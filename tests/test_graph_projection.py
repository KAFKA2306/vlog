from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import vlog_memory_domain
from vlog_memory_domain import (
    EpisodeCandidate,
    EpisodeProjectionPayload,
    EvidenceRef,
    MemoryClaim,
    MemoryStatus,
    ProjectionStatus,
    build_episode_payload,
    run_projection,
)
from vlog_memory_domain.models import Episode, Utterance

T0 = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
HASH = "a" * 64


def make_candidate(
    text: str = "今日はUnityでワールドを作って友達と話した",
    *,
    started: datetime = T0,
    with_claim: bool = True,
    claim_status: MemoryStatus = MemoryStatus.ACCEPTED,
    foreign_claim: bool = False,
) -> EpisodeCandidate:
    source_id = str(uuid4())
    episode = Episode(
        started_at=started,
        ended_at=started + timedelta(minutes=30),
        source_object_ids=(source_id,),
    )
    utterance = Utterance(
        episode_id=episode.id,
        started_at=started,
        ended_at=started + timedelta(seconds=5),
        text=text,
    )
    claims = ()
    if with_claim:
        evidence_episode = str(uuid4()) if foreign_claim else episode.id
        claims = (
            MemoryClaim(
                claim_type="activity",
                subject_entity_id=str(uuid4()),
                value="builds VRChat worlds",
                valid_from=started,
                evidence=(
                    EvidenceRef(
                        source_object_id=source_id,
                        episode_id=evidence_episode,
                        utterance_id=utterance.id,
                    ),
                ),
                status=claim_status,
            ),
        )
    return EpisodeCandidate(
        episode=episode,
        utterances=(utterance,),
        claims=claims,
        source_hash=HASH,
        pipeline_version="pipe-1",
    )


@dataclass
class FakeSink:
    fail: bool = False
    calls: list = field(default_factory=list)

    def project(self, payload) -> str:
        if self.fail:
            raise ConnectionError("graph down")
        self.calls.append(payload)
        return f"graph-{payload.projection_key[:8]}"


@dataclass
class FakeLedger:
    done: dict = field(default_factory=dict)
    failures: dict = field(default_factory=dict)

    def is_projected(self, projection_key: str) -> bool:
        return projection_key in self.done

    def mark_projected(self, payload, graph_ref: str) -> None:
        self.done[payload.projection_key] = (payload, graph_ref)
        self.failures.pop(payload.projection_key, None)

    def record_failure(self, payload, error: str) -> None:
        self.failures[payload.projection_key] = error


def build(candidate: EpisodeCandidate):
    return build_episode_payload(candidate, projection_version="p1")


def build_payload(candidate: EpisodeCandidate, version: str = "p1"):
    result = build_episode_payload(candidate, projection_version=version)
    assert isinstance(result, EpisodeProjectionPayload)
    return result


def test_payload_keeps_provenance_and_stable_identity() -> None:
    candidate = make_candidate()
    payload = build_payload(candidate)
    again = build_payload(candidate)
    assert payload.projection_key == again.projection_key
    assert payload.episode_id == candidate.episode.id
    assert payload.reference_time == T0
    assert payload.source_hash == HASH
    assert payload.pipeline_version == "pipe-1"
    assert payload.projection_version == "p1"
    assert len(payload.facts) == 1
    assert payload.facts[0].evidence == candidate.claims[0].evidence
    assert candidate.episode.id in payload.source_description
    assert "builds VRChat worlds" in payload.body


def test_projection_key_changes_with_version() -> None:
    candidate = make_candidate()
    other = build_payload(candidate, "p2")
    assert other.projection_key != build_payload(candidate).projection_key


def test_candidate_claims_are_not_projected_as_facts() -> None:
    payload = build_payload(make_candidate(claim_status=MemoryStatus.CANDIDATE))
    assert payload.facts == ()
    assert "builds VRChat worlds" not in payload.body


def test_low_information_is_skipped() -> None:
    result = build(make_candidate(text="えっと"))
    assert result.status is ProjectionStatus.SKIPPED
    assert result.reason == "low_information"


def test_claim_pointing_to_other_episode_is_rejected() -> None:
    result = build(make_candidate(foreign_claim=True))
    assert result.status is ProjectionStatus.REJECTED
    assert result.reason == "claim_evidence_outside_episode"


def test_run_is_idempotent_and_audited() -> None:
    sink, ledger = FakeSink(), FakeLedger()
    candidates = [make_candidate(), make_candidate(started=T0 + timedelta(days=1))]
    first = run_projection(candidates, sink, ledger, projection_version="p1")
    second = run_projection(candidates, sink, ledger, projection_version="p1")
    assert (first.projected, first.duplicate) == (2, 0)
    assert (second.projected, second.duplicate) == (0, 2)
    assert len(sink.calls) == 2


def test_audit_counts_skipped_and_rejected() -> None:
    audit = run_projection(
        [
            make_candidate(),
            make_candidate(text="うん", started=T0 + timedelta(hours=1)),
            make_candidate(foreign_claim=True, started=T0 + timedelta(hours=2)),
        ],
        FakeSink(),
        FakeLedger(),
        projection_version="p1",
    )
    assert audit.as_dict() == {
        "projected": 1,
        "duplicate": 0,
        "skipped": 1,
        "rejected": 1,
        "failed": 0,
        "dry_run": False,
    }


def test_sink_failure_is_isolated_and_retryable() -> None:
    ledger = FakeLedger()
    candidates = [make_candidate()]
    failing = run_projection(
        candidates, FakeSink(fail=True), ledger, projection_version="p1"
    )
    assert failing.failed == 1
    assert len(ledger.failures) == 1
    assert ledger.done == {}
    retry = run_projection(candidates, FakeSink(), ledger, projection_version="p1")
    assert retry.projected == 1
    assert ledger.failures == {}


def test_one_failure_does_not_block_other_episodes() -> None:
    class FlakySink(FakeSink):
        blipped: bool = False

        def project(self, payload) -> str:
            if not self.blipped:
                self.blipped = True
                raise ConnectionError("blip")
            return super().project(payload)

    audit = run_projection(
        [make_candidate(), make_candidate(started=T0 + timedelta(days=1))],
        FlakySink(),
        FakeLedger(),
        projection_version="p1",
    )
    assert (audit.projected, audit.failed) == (1, 1)


def test_dry_run_has_no_side_effects() -> None:
    sink, ledger = FakeSink(), FakeLedger()
    audit = run_projection(
        [make_candidate()], sink, ledger, projection_version="p1", dry_run=True
    )
    assert audit.projected == 1 and audit.dry_run
    assert sink.calls == [] and ledger.done == {}


def test_processing_order_is_deterministic() -> None:
    a = make_candidate(started=T0 + timedelta(days=2))
    b = make_candidate(started=T0)
    sink = FakeSink()
    run_projection([a, b], sink, FakeLedger(), projection_version="p1")
    assert [p.reference_time for p in sink.calls] == [T0, T0 + timedelta(days=2)]


def test_domain_package_has_no_graphiti_import() -> None:
    root = Path(vlog_memory_domain.__file__).parent
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "import graphiti" not in text and "from graphiti" not in text
