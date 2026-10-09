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
