from __future__ import annotations

import json
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "packages" / "memory-domain" / "src"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "ingestion" / "src"))

from vlog_ingestion import (  # noqa: E402
    BackfillCandidateStatus,
    BackfillSourceKind,
    BackfillSourceRecord,
    SpeakerKind,
    dry_run_social_mirror_backfill,
)
from vlog_memory_domain import SocialMirrorEvidenceLevel  # noqa: E402

FIXTURE = REPO_ROOT / "tests" / "fixtures" / "social_mirror_backfill.jsonl"


def load_fixture() -> tuple[BackfillSourceRecord, ...]:
    records = []
    for line in FIXTURE.read_text(encoding="utf-8").splitlines():
        payload = json.loads(line)
        records.append(
            BackfillSourceRecord(
                source_object_id=payload["source_object_id"],
                episode_id=payload["episode_id"],
                subject_entity_id=payload["subject_entity_id"],
                utterance_id=payload.get("utterance_id"),
                recorded_at=datetime.fromisoformat(payload["recorded_at"]),
                source_kind=BackfillSourceKind(payload["source_kind"]),
                speaker_kind=SpeakerKind(payload["speaker_kind"]),
                speaker_label=payload["speaker_label"],
                text=payload["text"],
            )
        )
    return tuple(records)


def test_only_raw_other_utterance_is_verified_quote_candidate() -> None:
    report = dry_run_social_mirror_backfill(load_fixture())

    verified = [
        candidate
        for candidate in report.candidates
        if candidate.status is BackfillCandidateStatus.VERIFIED_QUOTE_CANDIDATE
    ]

    assert len(verified) == 1
    assert verified[0].source_kind is BackfillSourceKind.RAW_TRANSCRIPT
    assert verified[0].text == "詳しすぎる"
    assert (
        verified[0].suggested_evidence_level is SocialMirrorEvidenceLevel.DIRECT_QUOTE
    )
    assert verified[0].reason == "raw_utterance_verbatim_match"


def test_summary_and_diary_quotes_remain_review_candidates() -> None:
    report = dry_run_social_mirror_backfill(load_fixture())
    derived = [
        candidate
        for candidate in report.candidates
        if candidate.source_kind
        in {BackfillSourceKind.SUMMARY, BackfillSourceKind.DIARY}
        and candidate.text is not None
    ]

    assert {candidate.text for candidate in derived} == {"研究しすぎ", "魔王が来た"}
    assert all(
        candidate.status is BackfillCandidateStatus.REVIEW_CANDIDATE
        for candidate in derived
    )
    assert all(
        candidate.suggested_evidence_level is SocialMirrorEvidenceLevel.PARAPHRASE
        for candidate in derived
    )


def test_unverified_speaker_boundary_never_auto_verifies_raw_text() -> None:
    report = dry_run_social_mirror_backfill(load_fixture())
    candidate = next(
        item
        for item in report.candidates
        if item.source_object_id == "55555555-5555-4555-8555-555555555555"
    )

    assert candidate.status is BackfillCandidateStatus.REVIEW_CANDIDATE
    assert candidate.reason == "speaker_boundary_unverified"
    assert candidate.suggested_evidence_level is SocialMirrorEvidenceLevel.PARAPHRASE


def test_self_speech_and_derived_text_without_quote_marker_are_skipped() -> None:
    report = dry_run_social_mirror_backfill(load_fixture())
    skipped_by_source = {
        item.source_object_id: item.reason
        for item in report.candidates
        if item.status is BackfillCandidateStatus.SKIPPED
    }

    assert skipped_by_source["44444444-4444-4444-8444-444444444444"] == (
        "speaker_is_self"
    )
    assert skipped_by_source["66666666-6666-4666-8666-666666666666"] == (
        "no_explicit_quote_marker"
    )


def test_rerun_is_idempotent_and_candidate_ids_are_deterministic() -> None:
    first = dry_run_social_mirror_backfill(load_fixture())
    second = dry_run_social_mirror_backfill(tuple(reversed(load_fixture())))

    assert first == second
    assert [item.candidate_id for item in first.candidates] == [
        item.candidate_id for item in second.candidates
    ]


def test_date_range_is_inclusive() -> None:
    report = dry_run_social_mirror_backfill(
        load_fixture(),
        start_date=date(2026, 8, 2),
        end_date=date(2026, 8, 2),
    )

    assert {item.recorded_at.date() for item in report.candidates} == {date(2026, 8, 2)}
    assert report.total_sources == 2


def test_invalid_date_range_is_rejected() -> None:
    try:
        dry_run_social_mirror_backfill(
            load_fixture(),
            start_date=date(2026, 8, 3),
            end_date=date(2026, 8, 2),
        )
    except ValueError as exc:
        assert str(exc) == "start_date must be <= end_date"
    else:
        raise AssertionError("invalid date range must fail")


def test_report_counts_decision_reasons() -> None:
    report = dry_run_social_mirror_backfill(load_fixture())

    assert report.total_sources == 6
    assert report.verified_count == 1
    assert report.review_count == 3
    assert report.skipped_count == 2
    assert all(item.reason for item in report.candidates)


def test_cli_is_dry_run_and_does_not_modify_fixture() -> None:
    before = FIXTURE.read_bytes()
    completed = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "social_mirror_backfill.py"),
            "--input",
            str(FIXTURE),
            "--start-date",
            "2026-08-01",
            "--end-date",
            "2026-08-03",
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    payload = json.loads(completed.stdout)

    assert payload["dry_run"] is True
    assert payload["total_sources"] == 6
    assert payload["verified_quote_candidates"] == 1
    assert payload["review_candidates"] == 3
    assert payload["skipped"] == 2
    assert FIXTURE.read_bytes() == before
