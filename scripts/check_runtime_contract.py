#!/usr/bin/env python3
"""Fail when runtime configuration regresses to checkout-layout coupling."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PREFIXES = (
    ".github/workflows/",
    "infra/systemd/",
    "infra/windows/",
    "apps/capture-vrchat/src/",
)
RUNTIME_FILES = {"Taskfile.yaml"}
FORBIDDEN = {
    "PYTHONPATH": "runtime must use installed workspace packages",
    "USER_WORKING_DIR": "tasks must resolve from the root Taskfile",
    "python3.12/site-packages/nvidia": "GPU libraries must be discovered at runtime",
    "python -m src": "legacy src package entrypoints are forbidden",
    "from src": "legacy src imports are forbidden",
    "import src": "legacy src imports are forbidden",
}


def tracked_files() -> list[str]:
    raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
    return [item.decode("utf-8") for item in raw.split(b"\0") if item]


def violations(paths: list[str] | None = None) -> list[str]:
    failures: list[str] = []
    for relative in paths or tracked_files():
        if relative not in RUNTIME_FILES and not relative.startswith(RUNTIME_PREFIXES):
            continue
        path = ROOT / relative
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for token, reason in FORBIDDEN.items():
            if token in text:
                failures.append(f"{relative}: contains {token!r}: {reason}")
    return failures


def main() -> int:
    failures = violations()
    if not failures:
        print("runtime-contract-check: PASS")
        return 0
    for failure in failures:
        print(f"runtime-contract-check: FAIL: {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
