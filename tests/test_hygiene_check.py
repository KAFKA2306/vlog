from pathlib import Path

from scripts import hygiene_check


def test_scan_finds_audio_at_or_below_threshold(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(hygiene_check, "_probe_stream", lambda _path: None)
    recordings = tmp_path / "recordings"
    recordings.mkdir()
    (recordings / "empty.flac").write_bytes(b"")
    (recordings / "header.flac").write_bytes(b"x" * 100)
    (recordings / "usable.flac").write_bytes(b"x" * 101)
    (recordings / "notes.txt").write_bytes(b"")

    findings = hygiene_check.scan(recordings)

    assert [finding.path.name for finding in findings] == ["empty.flac", "header.flac"]


def test_quarantine_moves_files_without_overwriting(tmp_path: Path) -> None:
    recordings = tmp_path / "recordings"
    quarantine_dir = tmp_path / "quarantine"
    events = tmp_path / "events.jsonl"
    recordings.mkdir()
    first = recordings / "empty.flac"
    first.write_bytes(b"")
    existing = quarantine_dir / first.name
    quarantine_dir.mkdir()
    existing.write_bytes(b"previous")

    moved = hygiene_check.quarantine(
        hygiene_check.scan(recordings), quarantine_dir, events
    )

    assert moved == [quarantine_dir / "empty.flac.1"]
    assert not first.exists()
    assert existing.read_bytes() == b"previous"
    assert moved[0].exists()
    assert "recording_quarantined" in events.read_text(encoding="utf-8")
