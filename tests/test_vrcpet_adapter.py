from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "packages" / "memory-domain" / "src"))

import adapters.vrcpet.normalizer as normalizer_module  # noqa: E402
from adapters.vrcpet import (  # noqa: E402
    SourceBoundaryError,
    SourceFile,
    UnstableSourceError,
    associate_episode,
    build_companion_daily_view,
    build_ingestion_run,
    build_state_snapshot,
    deduplicate_observations,
    diff_profile,
    diff_vocabulary_counts,
    discover_source_paths,
    normalize_source,
    parse_observation,
    read_source_file,
)
from vlog_memory_domain import (  # noqa: E402
    Episode,
    PrivacyLevel,
    SourceKind,
    SourceObject,
)


def _source(relative_path: str, raw_bytes: bytes, *, mtime_ns: int = 1_700_000_000_000_000_000) -> SourceFile:
    return SourceFile(
        relative_path=relative_path,
        raw_bytes=raw_bytes,
        size_bytes=len(raw_bytes),
        mtime_ns=mtime_ns,
    )


def test_jsonl_malformed_line_is_isolated_without_losing_valid_records() -> None:
    parsed = parse_observation(
        "logs/2026-08-12.jsonl",
        b'{"text":"hello"}\n{"broken":\n{"text":"world"}\n',
    )

    assert [record["text"] for record in parsed.records] == ["hello", "world"]
    assert len(parsed.issues) == 1
    assert parsed.issues[0].code == "malformed_jsonl_line"
    assert parsed.issues[0].line_number == 2


def test_empty_source_is_valid_and_produces_no_records() -> None:
    parsed = parse_observation("logs/empty.jsonl", b"")
    assert parsed.records == ()
    assert parsed.issues == ()


def test_pet_log_preserves_unknown_text_and_malformed_json() -> None:
    parsed = parse_observation(
        "pet.log",
        b'plain operational line\n{"event":"ok"}\n{"broken":\n',
    )

    assert parsed.records[0] == {"raw_text": "plain operational line"}
    assert parsed.records[1] == {"event": "ok"}
    assert parsed.records[2]["raw_text"] == '{"broken":'
    assert parsed.issues[0].code == "malformed_pet_log_json"


def test_source_root_allowlist_and_path_escape_are_rejected(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "profile.json").write_text("{}", encoding="utf-8")

    with pytest.raises(SourceBoundaryError, match="allowlist"):
        read_source_file(
            outside,
            "profile.json",
            allowlisted_roots=(allowed,),
        )

    with pytest.raises(SourceBoundaryError, match="relative"):
        read_source_file(outside, "../outside/profile.json")


def test_reader_detects_source_changed_during_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "vrcpet"
    root.mkdir()
    path = root / "profile.json"
    path.write_text('{"name":"sui"}', encoding="utf-8")
    original_read_bytes = Path.read_bytes

    def changing_read_bytes(self: Path) -> bytes:
        value = original_read_bytes(self)
        if self == path:
            self.write_bytes(value + b" ")
        return value

    monkeypatch.setattr(Path, "read_bytes", changing_read_bytes)
    with pytest.raises(UnstableSourceError, match="changed while reading"):
        read_source_file(root, "profile.json")


def test_discovery_is_limited_to_observed_vrcpet_inputs(tmp_path: Path) -> None:
    root = tmp_path / "vrcpet"
    logs = root / "logs"
    logs.mkdir(parents=True)
    (logs / "2026-08-12.jsonl").write_text("{}\n", encoding="utf-8")
    (root / "pet.log").write_text("event\n", encoding="utf-8")
    (root / "profile.json").write_text("{}", encoding="utf-8")
    (root / "heard_nouns.json").write_text("{}", encoding="utf-8")
    (root / "secret.txt").write_text("must not be discovered", encoding="utf-8")

    assert discover_source_paths(root) == (
        "heard_nouns.json",
        "logs/2026-08-12.jsonl",
        "pet.log",
        "profile.json",
    )


def test_normalization_is_content_addressed_and_sanitizes_absolute_path(tmp_path: Path) -> None:
    raw = b'{"text":"same"}\n'
    first = normalize_source(
        _source("logs/a.jsonl", raw),
        parse_observation("logs/a.jsonl", raw),
    )
    renamed = normalize_source(
        _source("logs/renamed.jsonl", raw),
        parse_observation("logs/renamed.jsonl", raw),
    )
    changed = normalize_source(
        _source("logs/a.jsonl", b'{"text":"changed"}\n'),
        parse_observation("logs/a.jsonl", b'{"text":"changed"}\n'),
    )

    assert first.source_object.id == renamed.source_object.id
    assert first.source_hash == renamed.source_hash
    assert first.source_object.id != changed.source_object.id
    assert first.source_object.object_uri.startswith("private://vrcpet/conversation/")
    manifest_text = json.dumps(first.manifest, ensure_ascii=False)
    assert str(tmp_path) not in manifest_text
    assert first.manifest["metadata"]["source_relative_path"] == "logs/a.jsonl"


def test_duplicate_ingest_and_pipeline_version_are_idempotent() -> None:
    raw = b'{"text":"same"}\n'
    observation = normalize_source(
        _source("logs/a.jsonl", raw),
        parse_observation("logs/a.jsonl", raw),
    )
    duplicate = normalize_source(
        _source("logs/b.jsonl", raw),
        parse_observation("logs/b.jsonl", raw),
    )

    assert deduplicate_observations((observation, duplicate)) == (observation,)
    run = build_ingestion_run(
        observation,
        pipeline_version="human-memory-v2:vrcpet-1",
        at=datetime(2026, 8, 12, tzinfo=timezone.utc),
    )
    assert run.idempotency_key == (
        f"{observation.source_hash}:human-memory-v2:vrcpet-1"
    )


def test_state_snapshot_retains_exact_bytes_and_diff_is_explicit() -> None:
    profile_raw = b'{"favorite":"blue","mood":"curious"}'
    profile = normalize_source(
        _source("profile.json", profile_raw),
        parse_observation("profile.json", profile_raw),
    )
    snapshot = build_state_snapshot(profile, captured_on=date(2026, 8, 12))

    assert snapshot.raw_bytes == profile_raw
    assert snapshot.object_uri.startswith("private://vrcpet/snapshots/2026-08-12/profile/")
    profile_delta = diff_profile(
        {"favorite": "blue", "mood": "calm", "old": True},
        {"favorite": "blue", "mood": "curious", "new": 1},
    )
    assert profile_delta.added == {"new": 1}
    assert profile_delta.removed == {"old": True}
    assert profile_delta.changed == {"mood": ("calm", "curious")}

    vocabulary_delta = diff_vocabulary_counts(
        {"旅行": 2, "GPU": 4, "old": 1},
        {"旅行": 5, "GPU": 3, "京都": 1},
    )
    assert vocabulary_delta.new == {"京都": 1}
    assert vocabulary_delta.increased == {"旅行": (2, 5)}
    assert vocabulary_delta.decreased == {"GPU": (4, 3)}
    assert vocabulary_delta.missing == {"old": 1}


def test_observation_associates_with_existing_episode_without_memory_claim_promotion() -> None:
    primary = SourceObject(
        kind=SourceKind.AUDIO,
        object_uri="private://audio/session.flac",
        sha256="0" * 64,
        size_bytes=10,
        recorded_at=datetime(2026, 8, 12, tzinfo=timezone.utc),
        privacy=PrivacyLevel.PRIVATE,
    )
    episode = Episode(
        started_at=datetime(2026, 8, 12, tzinfo=timezone.utc),
        ended_at=datetime(2026, 8, 12, 1, tzinfo=timezone.utc),
        source_object_ids=(primary.id,),
    )
    raw = b'{"text":"Kyoto"}\n'
    observation = normalize_source(
        _source("logs/day.jsonl", raw),
        parse_observation("logs/day.jsonl", raw),
    )

    associated = associate_episode(episode, (observation, observation))
    assert associated.id == episode.id
    assert associated.source_object_ids == (primary.id, observation.source_object.id)
    assert not hasattr(normalizer_module, "MemoryClaim")


def test_end_to_end_daily_companion_view_is_rebuildable() -> None:
    conversation_raw = b'{"text":"travel"}\n{"broken":\n{"text":"Kyoto"}\n'
    profile_raw = b'{"favorite":"blue","mood":"curious"}'
    vocabulary_raw = '{"旅行":5,"GPU":3,"京都":1}'.encode()

    conversation = normalize_source(
        _source("logs/2026-08-12.jsonl", conversation_raw),
        parse_observation("logs/2026-08-12.jsonl", conversation_raw),
    )
    profile = normalize_source(
        _source("profile.json", profile_raw),
        parse_observation("profile.json", profile_raw),
    )
    vocabulary = normalize_source(
        _source("heard_nouns.json", vocabulary_raw),
        parse_observation("heard_nouns.json", vocabulary_raw),
    )
    snapshots = (
        build_state_snapshot(profile, captured_on=date(2026, 8, 12)),
        build_state_snapshot(vocabulary, captured_on=date(2026, 8, 12)),
    )
    vocabulary_delta = diff_vocabulary_counts(
        {"旅行": 2, "GPU": 4, "old": 1},
        {"旅行": 5, "GPU": 3, "京都": 1},
    )
    profile_delta = diff_profile(
        {"favorite": "blue", "mood": "calm"},
        {"favorite": "blue", "mood": "curious"},
    )

    view = build_companion_daily_view(
        day=date(2026, 8, 12),
        observations=(conversation, profile, vocabulary),
        snapshots=snapshots,
        current_counts={"旅行": 5, "GPU": 3, "京都": 1},
        vocabulary_diff=vocabulary_delta,
        profile_diff=profile_delta,
        pet_utterances=("こんにちは",),
    )
    rendered = view.render_markdown(pet_name="すい")

    assert view.conversation_records == 2
    assert view.parse_issues == 1
    assert view.snapshots == 2
    assert "# すいの目から見た2026-08-12" in rendered
    assert "京都" in rendered
    assert "mood" in rendered
    assert "こんにちは" in rendered
