from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from vlog_memory_domain import EpisodeProjectionPayload, EvidenceRef


@dataclass(frozen=True, slots=True)
class ProjectionTrace:
    projection_key: str
    graph_ref: str
    episode_id: str
    episode_name: str
    source_hash: str
    pipeline_version: str
    projection_version: str
    evidence: tuple[EvidenceRef, ...]


class JsonlProjectionLedger:
    """Append-only projection state. Rebuildable; never canonical memory."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def _events(self) -> list[dict]:
        if not self.path.exists():
            return []
        with self.path.open(encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    def _append(self, event: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    def _latest(self) -> dict[str, dict]:
        return {event["projection_key"]: event for event in self._events()}

    def is_projected(self, projection_key: str) -> bool:
        latest = self._latest().get(projection_key)
        return latest is not None and latest["status"] == "projected"

    def failed_keys(self) -> list[str]:
        return sorted(
            key for key, event in self._latest().items() if event["status"] == "failed"
        )

    def projected_events(self) -> list[dict]:
        return [e for e in self._latest().values() if e["status"] == "projected"]

    def mark_projected(self, payload: EpisodeProjectionPayload, graph_ref: str) -> None:
        self._append(self._event(payload, "projected", graph_ref=graph_ref))

    def record_failure(self, payload: EpisodeProjectionPayload, error: str) -> None:
        self._append(self._event(payload, "failed", error=error))

    @staticmethod
    def _event(payload: EpisodeProjectionPayload, status: str, **extra: str) -> dict:
        return {
            "projection_key": payload.projection_key,
            "status": status,
            "episode_id": payload.episode_id,
            "episode_name": payload.episode_name,
            "source_hash": payload.source_hash,
            "pipeline_version": payload.pipeline_version,
            "projection_version": payload.projection_version,
            "evidence": [asdict(ref) for ref in payload.evidence],
            **extra,
        }


def resolve_trace(
    ledger: JsonlProjectionLedger, graph_ref_or_name: str
) -> ProjectionTrace | None:
    for event in ledger.projected_events():
        if graph_ref_or_name in (event["graph_ref"], event["episode_name"]):
            return ProjectionTrace(
                projection_key=event["projection_key"],
                graph_ref=event["graph_ref"],
                episode_id=event["episode_id"],
                episode_name=event["episode_name"],
                source_hash=event["source_hash"],
                pipeline_version=event["pipeline_version"],
                projection_version=event["projection_version"],
                evidence=tuple(EvidenceRef(**ref) for ref in event["evidence"]),
            )
    return None
