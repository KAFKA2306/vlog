#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from vlog_capture.portability import runtime_directories
from vlog_ingestion import InventoryBuilder, InventoryConfig, write_inventory

REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a read-only inventory before Human Memory v2 migration.",
    )
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path. Defaults to VLOG_STATE_HOME/inventory/phase0-<UTC timestamp>.json.",
    )
    parser.add_argument(
        "--evidence-root",
        action="append",
        dest="evidence_roots",
        help="Repository-relative source root to inventory. Repeat to override defaults.",
    )
    parser.add_argument(
        "--fail-on-tracked-evidence",
        action="store_true",
        help="Exit 2 when evidence files are tracked by Git.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.expanduser().resolve()
    config_kwargs: dict[str, object] = {"repo_root": root}
    if args.evidence_roots:
        config_kwargs["evidence_roots"] = tuple(args.evidence_roots)
    inventory = InventoryBuilder(InventoryConfig(**config_kwargs)).build()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.output or (
        runtime_directories().state / "inventory" / f"phase0-{timestamp}.json"
    )
    output = output.expanduser()
    if not output.is_absolute():
        output = runtime_directories().state / output
    write_inventory(inventory, output)

    summary = inventory["summary"]
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    print(f"Inventory: {output}")
    print("No files were deleted, moved, or uploaded.")

    tracked_files = int(summary["tracked_files"])
    if args.fail_on_tracked_evidence and tracked_files:
        print(
            f"ERROR: {tracked_files} evidence files are tracked by Git.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
