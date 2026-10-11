from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from vlog_graphiti import (
    GraphitiProjectionSink,
    JsonlProjectionLedger,
    resolve_trace,
)
from vlog_memory_domain import run_projection

from tests.test_graph_projection import T0, build_payload, make_candidate


class FakeGraphiti:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[dict] = []

    async def add_episode(self, **kwargs) -> None:
        if self.fail:
            raise ConnectionError("down")
        self.calls.append(kwargs)


def test_sink_maps_payload_to_one_temporal_episode() -> None:
    client = FakeGraphiti()
    payload = build_payload(make_candidate())
    ref = GraphitiProjectionSink(client, group_id="vlog").project(payload)
    (call,) = client.calls
    assert call["reference_time"] == T0
    assert call["group_id"] == "vlog"
    assert call["name"] == payload.episode_name
    assert call["episode_body"] == payload.body
    assert call["source_description"] == payload.source_description
    assert call["uuid"] == ref
    assert str(UUID(ref)) == ref


def test_graph_uuid_is_stable_per_projection_key() -> None:
    payload = build_payload(make_candidate())
    a = GraphitiProjectionSink(FakeGraphiti(), group_id="vlog").project(payload)
    b = GraphitiProjectionSink(FakeGraphiti(), group_id="vlog").project(payload)
    assert a == b


def test_ledger_survives_restart_and_dedupes(tmp_path) -> None:
    path = tmp_path / "ledger.jsonl"
    client = FakeGraphiti()
    sink = GraphitiProjectionSink(client, group_id="vlog")
    candidates = [make_candidate(), make_candidate(started=T0 + timedelta(days=1))]
    run_projection(
        candidates, sink, JsonlProjectionLedger(path), projection_version="p1"
    )
    again = run_projection(
        candidates, sink, JsonlProjectionLedger(path), projection_version="p1"
    )
    assert again.duplicate == 2
    assert len(client.calls) == 2


def test_failure_recorded_then_retried(tmp_path) -> None:
    path = tmp_path / "ledger.jsonl"
    candidates = [make_candidate()]
    bad = run_projection(
        candidates,
        GraphitiProjectionSink(FakeGraphiti(fail=True), group_id="vlog"),
        JsonlProjectionLedger(path),
        projection_version="p1",
    )
    assert bad.failed == 1
    assert len(JsonlProjectionLedger(path).failed_keys()) == 1
    good = run_projection(
        candidates,
        GraphitiProjectionSink(FakeGraphiti(), group_id="vlog"),
        JsonlProjectionLedger(path),
        projection_version="p1",
    )
    assert good.projected == 1
    assert JsonlProjectionLedger(path).failed_keys() == []


def test_trace_resolves_graph_ref_to_canonical_episode_and_evidence(tmp_path) -> None:
    path = tmp_path / "ledger.jsonl"
    candidate = make_candidate()
    sink = GraphitiProjectionSink(FakeGraphiti(), group_id="vlog")
    run_projection(
        [candidate], sink, JsonlProjectionLedger(path), projection_version="p1"
    )
    payload = build_payload(candidate)
    trace = resolve_trace(JsonlProjectionLedger(path), sink.graph_uuid(payload))
    assert trace is not None
    assert trace.episode_id == candidate.episode.id
    assert trace.source_hash == payload.source_hash
    assert trace.evidence == candidate.claims[0].evidence
    by_name = resolve_trace(JsonlProjectionLedger(path), payload.episode_name)
    assert by_name is not None
    assert by_name.episode_id == candidate.episode.id


def test_trace_unknown_returns_none(tmp_path) -> None:
    assert resolve_trace(JsonlProjectionLedger(tmp_path / "l.jsonl"), "nope") is None
