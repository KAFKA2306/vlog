from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "packages" / "ingestion" / "src"))

from vlog_ingestion import InventoryBuilder, InventoryConfig, write_inventory  # noqa: E402


def test_inventory_hashes_files_without_modifying_sources(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    recordings = tmp_path / "data" / "recordings"
    recordings.mkdir(parents=True)
    source = recordings / "session.flac"
    source.write_bytes(b"evidence")
    before = source.stat()

    inventory = InventoryBuilder(InventoryConfig(repo_root=tmp_path)).build()
    output = tmp_path / "data" / "inventory" / "phase0.json"
    write_inventory(inventory, output)

    after = source.stat()
    assert source.read_bytes() == b"evidence"
    assert before.st_size == after.st_size
    assert inventory["policy"] == {
        "operation": "read-only",
        "deletes_files": False,
        "moves_files": False,
        "uploads_files": False,
        "hash_algorithm": "sha256",
    }
    assert inventory["summary"]["files"] == 1
    assert inventory["files"][0]["path"] == "data/recordings/session.flac"
    assert len(inventory["files"][0]["sha256"]) == 64
    assert output.exists()


def test_inventory_reports_duplicate_content(tmp_path: Path) -> None:
    first_root = tmp_path / "data" / "recordings"
    second_root = tmp_path / "data" / "transcripts"
    first_root.mkdir(parents=True)
    second_root.mkdir(parents=True)
    (first_root / "a.flac").write_bytes(b"same")
    (second_root / "a.txt").write_bytes(b"same")

    inventory = InventoryBuilder(InventoryConfig(repo_root=tmp_path)).build()

    assert inventory["summary"]["duplicate_hash_groups"] == 1
    assert inventory["duplicate_hashes"][0]["paths"] == [
        "data/recordings/a.flac",
        "data/transcripts/a.txt",
    ]
