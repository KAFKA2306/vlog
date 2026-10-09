import argparse
import hashlib
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

LARGE_BYTES = 50 * 1024 * 1024
DATA_DIR = "data"
CHUNK_BYTES = 1024 * 1024

SCHEMA = """
CREATE TABLE IF NOT EXISTS dim_asset (
    asset_key TEXT PRIMARY KEY,
    zone TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS dim_scan (
    scan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    scanned_at TEXT NOT NULL,
    git_head TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fact_asset_state (
    scan_id INTEGER NOT NULL REFERENCES dim_scan(scan_id),
    asset_key TEXT NOT NULL REFERENCES dim_asset(asset_key),
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    PRIMARY KEY (scan_id, asset_key)
);
CREATE TABLE IF NOT EXISTS fact_processing (
    asset_key TEXT NOT NULL REFERENCES dim_asset(asset_key),
    stage TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    processed_at TEXT NOT NULL,
    PRIMARY KEY (asset_key, stage)
);
"""


def _git_candidates(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-co", "--exclude-standard", "-z"],
        check=True,
        capture_output=True,
    )
    return [item for item in result.stdout.decode("utf-8").split("\0") if item]


def _data_candidates(root: Path) -> list[str]:
    data = root / DATA_DIR
    if not data.is_dir():
        return []
    return [
        path.relative_to(root).as_posix() for path in data.rglob("*") if path.is_file()
    ]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _zone(key: str) -> str:
    return "data" if key.startswith(f"{DATA_DIR}/") else "repo"


def _git_head(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--verify", "-q", "HEAD"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _connect(db: Path) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    conn.executescript(SCHEMA)
    return conn


def _latest_scan_id(conn: sqlite3.Connection, offset: int = 0) -> int | None:
    row = conn.execute(
        "SELECT scan_id FROM dim_scan ORDER BY scan_id DESC LIMIT 1 OFFSET ?",
        (offset,),
    ).fetchone()
    return row[0] if row else None


def scan(root: Path, db: Path) -> int:
    keys = sorted(set(_git_candidates(root)) | set(_data_candidates(root)))
    with _connect(db) as conn:
        cursor = conn.execute(
            "INSERT INTO dim_scan (scanned_at, git_head) VALUES (?, ?)",
            (datetime.now(timezone.utc).isoformat(), _git_head(root)),
        )
        scan_id = cursor.lastrowid
        for key in keys:
            path = root / key
            if path.resolve() == db.resolve():
                continue
            if not path.is_file() or path.stat().st_size > LARGE_BYTES:
                continue
            conn.execute(
                "INSERT OR IGNORE INTO dim_asset (asset_key, zone) VALUES (?, ?)",
                (key, _zone(key)),
            )
            conn.execute(
                "INSERT INTO fact_asset_state (scan_id, asset_key, sha256, size_bytes) VALUES (?, ?, ?, ?)",
                (scan_id, key, _sha256(path), path.stat().st_size),
            )
    return scan_id


def _states(conn: sqlite3.Connection, scan_id: int) -> dict[str, str]:
    rows = conn.execute(
        "SELECT asset_key, sha256 FROM fact_asset_state WHERE scan_id = ?",
        (scan_id,),
    )
    return dict(rows.fetchall())


def diff_latest(db: Path) -> list[tuple[str, str]]:
    with _connect(db) as conn:
        current_id = _latest_scan_id(conn)
        previous_id = _latest_scan_id(conn, offset=1)
        if current_id is None or previous_id is None:
            return []
        current = _states(conn, current_id)
        previous = _states(conn, previous_id)
    changes = [("added", key) for key in current.keys() - previous.keys()]
    changes += [("removed", key) for key in previous.keys() - current.keys()]
    changes += [
        ("changed", key)
        for key in current.keys() & previous.keys()
        if current[key] != previous[key]
    ]
    return sorted(changes)


def mark_processed(db: Path, key: str, stage: str) -> None:
    with _connect(db) as conn:
        scan_id = _latest_scan_id(conn)
        row = conn.execute(
            "SELECT sha256 FROM fact_asset_state WHERE scan_id = ? AND asset_key = ?",
            (scan_id, key),
        ).fetchone()
        conn.execute(
            "INSERT OR REPLACE INTO fact_processing (asset_key, stage, sha256, processed_at) VALUES (?, ?, ?, ?)",
            (key, stage, row[0], datetime.now(timezone.utc).isoformat()),
        )


def unprocessed(db: Path, stage: str) -> list[str]:
    with _connect(db) as conn:
        scan_id = _latest_scan_id(conn)
        if scan_id is None:
            return []
        rows = conn.execute(
            """
            SELECT s.asset_key
            FROM fact_asset_state AS s
            LEFT JOIN fact_processing AS p
              ON p.asset_key = s.asset_key AND p.stage = ? AND p.sha256 = s.sha256
            WHERE s.scan_id = ? AND p.asset_key IS NULL
            ORDER BY s.asset_key
            """,
            (stage, scan_id),
        ).fetchall()
    return [row[0] for row in rows]


def _main() -> None:
    parser = argparse.ArgumentParser(description="VLog asset star-schema manifest")
    parser.add_argument("command", choices=["scan", "diff", "unprocessed"])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--db", type=Path, default=Path("data/asset_manifest.sqlite"))
    parser.add_argument("--stage", default="")
    args = parser.parse_args()
    if args.command == "scan":
        print(f"scan_id={scan(args.root, args.db)}")
    elif args.command == "diff":
        for kind, key in diff_latest(args.db):
            print(f"{kind}\t{key}")
    else:
        for key in unprocessed(args.db, args.stage):
            print(key)


if __name__ == "__main__":
    _main()
