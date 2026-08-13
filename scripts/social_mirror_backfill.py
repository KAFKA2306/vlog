from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "packages" / "memory-domain" / "src"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "ingestion" / "src"))

from vlog_ingestion import (  # noqa: E402
    BackfillSourceKind,
    BackfillSourceRecord,
    SpeakerKind,
    dry_run_social_mirror_backfill,
)


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _load_jsonl(path: Path) -> tuple[BackfillSourceRecord, ...]:
    records: list[BackfillSourceRecord] = []
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        try:
            records.append(
                BackfillSourceRecord(
                    source_object_id=payload["source_object_id"],
                    episode_id=payload["episode_id"],
                    subject_entity_id=payload["subject_entity_id"],
                    recorded_at=datetime.fromisoformat(payload["recorded_at"]),
                    source_kind=BackfillSourceKind(payload["source_kind"]),
                    text=payload["text"],
                    utterance_id=payload.get("utterance_id"),
                    speaker_kind=SpeakerKind(payload.get("speaker_kind", "unknown")),
                    speaker_label=payload.get("speaker_label", "unknown"),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid record at line {line_number}: {exc}") from exc
    return tuple(records)


def _serialize(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    raise TypeError(f"cannot serialize {type(value).__name__}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Dry-run Social Mirror candidate extraction from an immutable JSONL source "
            "manifest. This command never persists MemoryClaim objects."
        )
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--start-date", help="Inclusive YYYY-MM-DD boundary")
    parser.add_argument("--end-date", help="Inclusive YYYY-MM-DD boundary")
    args = parser.parse_args()

    report = dry_run_social_mirror_backfill(
        _load_jsonl(args.input),
        start_date=_parse_date(args.start_date),
        end_date=_parse_date(args.end_date),
    )
    output = {
        "dry_run": True,
        "total_sources": report.total_sources,
        "verified_quote_candidates": report.verified_count,
        "review_candidates": report.review_count,
        "skipped": report.skipped_count,
        "candidates": [asdict(candidate) for candidate in report.candidates],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, default=_serialize))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
