from pathlib import Path

import pytest
from vlog_capture.portability import RuntimeDirectories

from scripts.migrate_runtime_state import plan


def homes(tmp_path: Path) -> RuntimeDirectories:
    return RuntimeDirectories(
        config=tmp_path / "config",
        data=tmp_path / "data-home",
        state=tmp_path / "state-home",
        cache=tmp_path / "cache",
    )


def test_runtime_state_migration_is_non_destructive_and_hash_verified(
    tmp_path: Path,
) -> None:
    legacy = tmp_path / "repo-data"
    recording = legacy / "recordings" / "sample.wav"
    recording.parent.mkdir(parents=True)
    recording.write_bytes(b"vlog-audio")

    result = plan(legacy, homes(tmp_path), apply=True)

    target = tmp_path / "data-home" / "recordings" / "sample.wav"
    assert recording.read_bytes() == b"vlog-audio"
    assert target.read_bytes() == b"vlog-audio"
    assert result[0].sha256
    assert result[0].action == "copy"


def test_runtime_state_migration_rejects_conflicting_target(tmp_path: Path) -> None:
    legacy = tmp_path / "repo-data"
    source = legacy / "summaries" / "20260821.txt"
    source.parent.mkdir(parents=True)
    source.write_text("source", encoding="utf-8")

    target = tmp_path / "data-home" / "summaries" / "20260821.txt"
    target.parent.mkdir(parents=True)
    target.write_text("different", encoding="utf-8")

    with pytest.raises(RuntimeError, match="target conflict"):
        plan(legacy, homes(tmp_path), apply=True)
