import sqlite3
import subprocess
from pathlib import Path

from scripts import asset_manifest


def make_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / ".gitignore").write_text("ignored/\n", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "a.md").write_text("alpha", encoding="utf-8")
    (root / "ignored").mkdir()
    (root / "ignored" / "skip.txt").write_text("skip", encoding="utf-8")


def test_scan_records_tracked_and_untracked_but_not_ignored(tmp_path: Path) -> None:
    make_repo(tmp_path)
    db = tmp_path / "manifest.sqlite"
    asset_manifest.scan(tmp_path, db)
    with sqlite3.connect(db) as conn:
        rows = dict(conn.execute("SELECT asset_key, sha256 FROM fact_asset_state"))
    assert "docs/a.md" in rows
    assert "ignored/skip.txt" not in rows


def test_diff_reports_added_changed_removed(tmp_path: Path) -> None:
    make_repo(tmp_path)
    db = tmp_path / "manifest.sqlite"
    asset_manifest.scan(tmp_path, db)
    (tmp_path / "docs" / "a.md").write_text("beta", encoding="utf-8")
    (tmp_path / "docs" / "b.md").write_text("new", encoding="utf-8")
    asset_manifest.scan(tmp_path, db)
    assert asset_manifest.diff_latest(db) == [
        ("added", "docs/b.md"),
        ("changed", "docs/a.md"),
    ]
    (tmp_path / "docs" / "b.md").unlink()
    asset_manifest.scan(tmp_path, db)
    assert asset_manifest.diff_latest(db) == [("removed", "docs/b.md")]


def test_processed_state_resets_when_content_changes(tmp_path: Path) -> None:
    make_repo(tmp_path)
    db = tmp_path / "manifest.sqlite"
    asset_manifest.scan(tmp_path, db)
    for key in asset_manifest.unprocessed(db, "summarize"):
        asset_manifest.mark_processed(db, key, "summarize")
    assert asset_manifest.unprocessed(db, "summarize") == []
    (tmp_path / "docs" / "a.md").write_text("beta", encoding="utf-8")
    asset_manifest.scan(tmp_path, db)
    assert asset_manifest.unprocessed(db, "summarize") == ["docs/a.md"]


def test_link_mochio_records_purchase_and_releases_idempotently(tmp_path: Path) -> None:
    config = tmp_path / "mochio.yaml"
    config.write_text(
        "product:\n  name: ムチォ\n  purchased_on: 2026-08-11\n"
        "releases:\n"
        "  - version: 1.0.0\n    released_on: 2026-07-28\n    requires_unity_update: false\n"
        "  - version: 1.6.0\n    released_on: 2026-08-14\n    requires_unity_update: true\n",
        encoding="utf-8",
    )
    db = tmp_path / "manifest.sqlite"
    asset_manifest.link_mochio(db, config)
    asset_manifest.link_mochio(db, config)
    with sqlite3.connect(db) as conn:
        events = conn.execute(
            "SELECT event_date, kind, ref FROM fact_mochio_event ORDER BY event_date"
        ).fetchall()
    assert events == [
        ("2026-07-28", "release", "1.0.0"),
        ("2026-08-11", "purchase", "ムチォ"),
        ("2026-08-14", "release", "1.6.0"),
    ]


def test_mark_hygiene_processes_only_unflagged_audio(tmp_path: Path) -> None:
    make_repo(tmp_path)
    archives = tmp_path / "data" / "archives"
    archives.mkdir(parents=True)
    (archives / "good.flac").write_bytes(b"x" * 200)
    (archives / "bad.flac").write_bytes(b"")
    db = tmp_path / "manifest.sqlite"
    asset_manifest.scan(tmp_path, db)
    marked = asset_manifest.mark_hygiene(
        db, tmp_path, archives, flagged={"data/archives/bad.flac"}
    )
    assert marked == 1
    assert asset_manifest.unprocessed(db, "hygiene") == [
        ".gitignore",
        "data/archives/bad.flac",
        "docs/a.md",
    ]


def test_link_mochio_days_marks_nonempty_log_days_without_reading_content(tmp_path: Path) -> None:
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "2026-08-11.jsonl").write_text('{"secret": "not read"}\n', encoding="utf-8")
    (logs / "2026-08-12.jsonl").write_text("", encoding="utf-8")
    (logs / "pet.log").write_text("ignored", encoding="utf-8")
    db = tmp_path / "manifest.sqlite"
    asset_manifest.link_mochio_days(db, logs)
    with sqlite3.connect(db) as conn:
        rows = conn.execute(
            "SELECT event_date, kind, ref FROM fact_mochio_event WHERE kind = 'active_day'"
        ).fetchall()
    assert rows == [("2026-08-11", "active_day", "2026-08-11.jsonl")]
