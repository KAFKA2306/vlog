from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from src.infrastructure.settings import settings

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
COGNEE_QUEUE_PATH = _PROJECT_ROOT / "data" / "cognee_queue.yaml"

_AUDIO_SUFFIXES = {".wav", ".flac", ".mp3"}


@dataclass(frozen=True)
class DailyWorkloadCounts:
    recordings_pending: int
    transcript_days_pending: int
    summary_days_pending: int
    novel_days_pending: int
    cognee_pending: int
    cognee_processing: int
    cognee_failed: int
    cognee_batch_size: int

    @property
    def workload_score(self) -> int:
        return (
            self.recordings_pending
            + self.transcript_days_pending
            + self.summary_days_pending
            + self.novel_days_pending
            + self.cognee_pending
            + self.cognee_processing
            + (2 * self.cognee_failed)
        )

    @property
    def cognee_batches_remaining(self) -> int:
        if self.cognee_pending <= 0:
            return 0
        return math.ceil(self.cognee_pending / max(self.cognee_batch_size, 1))

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["workload_score"] = self.workload_score
        payload["cognee_batches_remaining"] = self.cognee_batches_remaining
        return payload


@dataclass(frozen=True)
class DailyWorkloadPlan:
    counts: DailyWorkloadCounts
    next_action: str
    next_action_target: int
    next_action_limit: int | None

    def to_dict(self) -> dict:
        return {
            "counts": self.counts.to_dict(),
            "next_action": self.next_action,
            "next_action_target": self.next_action_target,
            "next_action_limit": self.next_action_limit,
        }

    def format_lines(self) -> list[str]:
        counts = self.counts
        lines = [
            "Daily workload plan",
            (
                "  recordings_pending="
                f"{counts.recordings_pending} "
                "transcript_days_pending="
                f"{counts.transcript_days_pending} "
                "summary_days_pending="
                f"{counts.summary_days_pending} "
                "novel_days_pending="
                f"{counts.novel_days_pending}"
            ),
            (
                "  cognee pending="
                f"{counts.cognee_pending} "
                f"processing={counts.cognee_processing} "
                f"failed={counts.cognee_failed} "
                f"batch_size={counts.cognee_batch_size} "
                f"batches_remaining={counts.cognee_batches_remaining}"
            ),
            f"  workload_score={counts.workload_score}",
            (
                "  next_action="
                f"{self.next_action} target={self.next_action_target}"
                + (
                    f" limit={self.next_action_limit}"
                    if self.next_action_limit is not None
                    else ""
                )
            ),
        ]
        return lines

    def format_text(self) -> str:
        return "\n".join(self.format_lines())


class DailyWorkloadPlanner:
    def collect(self) -> DailyWorkloadPlan:
        recordings_pending = self._count_pending_recordings()
        transcript_dates = self._extract_dates(settings.transcript_dir.glob("*.txt"))
        summary_dates = self._extract_dates(settings.summary_dir.glob("*_summary.txt"))
        novel_dates = self._extract_dates(settings.novel_out_dir.glob("*.md"))
        evaluation_dates = self._extract_dates(
            (settings.summary_dir.parent / "evaluations").glob("*.json")
        )

        transcript_days_pending = len(transcript_dates - summary_dates)
        summary_days_pending = len(summary_dates - novel_dates)
        novel_days_pending = len((summary_dates & novel_dates) - evaluation_dates)

        cognee_stats = self._load_cognee_stats()
        counts = DailyWorkloadCounts(
            recordings_pending=recordings_pending,
            transcript_days_pending=transcript_days_pending,
            summary_days_pending=summary_days_pending,
            novel_days_pending=novel_days_pending,
            cognee_pending=cognee_stats["pending"],
            cognee_processing=cognee_stats["processing"],
            cognee_failed=cognee_stats["failed"],
            cognee_batch_size=cognee_stats["batch_size"],
        )

        next_action, next_target, next_limit = self._next_action(counts)
        return DailyWorkloadPlan(
            counts=counts,
            next_action=next_action,
            next_action_target=next_target,
            next_action_limit=next_limit,
        )

    def _count_pending_recordings(self) -> int:
        if not settings.recording_dir.exists():
            return 0
        pending = 0
        for audio_path in settings.recording_dir.glob("*"):
            if audio_path.suffix.lower() not in _AUDIO_SUFFIXES:
                continue
            if not self._transcript_exists_for(audio_path):
                pending += 1
        return pending

    def _transcript_exists_for(self, audio_path: Path) -> bool:
        stem = audio_path.stem
        return any(
            path.exists()
            for path in (
                settings.transcript_dir / f"{stem}.txt",
                settings.transcript_dir / f"cleaned_{stem}.txt",
            )
        )

    def _extract_dates(self, paths) -> set[str]:
        dates: set[str] = set()
        for path in paths:
            match = re.search(r"(\d{8})", Path(path).stem)
            if match:
                dates.add(match.group(1))
        return dates

    def _load_cognee_stats(self) -> dict[str, int]:
        if not COGNEE_QUEUE_PATH.exists():
            return {"pending": 0, "processing": 0, "failed": 0, "batch_size": 5}

        queue = yaml.safe_load(COGNEE_QUEUE_PATH.read_text(encoding="utf-8")) or {}
        files = queue.get("files", [])
        stats = {"pending": 0, "processing": 0, "failed": 0}
        for entry in files:
            status = entry.get("status", "pending")
            if status in stats:
                stats[status] += 1
        return {
            "pending": stats["pending"],
            "processing": stats["processing"],
            "failed": stats["failed"],
            "batch_size": int(queue.get("batch_size", 5) or 5),
        }

    def _next_action(self, counts: DailyWorkloadCounts) -> tuple[str, int, int | None]:
        if counts.recordings_pending > 0:
            return ("transcribe", counts.recordings_pending, None)
        if counts.transcript_days_pending > 0:
            return ("summarize", counts.transcript_days_pending, None)
        if counts.summary_days_pending > 0:
            return ("novelize", counts.summary_days_pending, None)
        if counts.novel_days_pending > 0:
            limit = min(counts.novel_days_pending, counts.cognee_batch_size)
            return ("evaluate", counts.novel_days_pending, limit)

        target = min(counts.cognee_pending, counts.cognee_batch_size)
        return ("cognee_ingest", target, counts.cognee_batch_size)


def collect_daily_workload() -> DailyWorkloadPlan:
    return DailyWorkloadPlanner().collect()


def render_daily_workload(plan: DailyWorkloadPlan) -> str:
    return plan.format_text()


def daily_workload_json(plan: DailyWorkloadPlan) -> str:
    return json.dumps(plan.to_dict(), ensure_ascii=False, indent=2)
