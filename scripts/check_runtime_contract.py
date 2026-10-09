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
    "scripts/",
)
RUNTIME_FILES = {"Taskfile.yaml"}
FORBIDDEN = {
    "PYTHONPATH": "runtime must use installed workspace packages",
    "sys.path.insert": "scripts must use installed workspace packages",
    "USER_WORKING_DIR": "tasks must resolve from the root Taskfile",
    "python3.12/site-packages/nvidia": "GPU libraries must be discovered at runtime",
    "python -m src": "retired src package entrypoints are forbidden",
    "from src": "retired src imports are forbidden",
    "import src": "retired src imports are forbidden",
    "source .env": "shell dotenv parsing is not a configuration authority",
    ". ./.env": "shell dotenv parsing is not a configuration authority",
    "load_dotenv()": "runtime configuration must use Settings and explicit VLOG_ENV_FILE",
    "EnvironmentFile=@VLOG_ROOT@/.env": "systemd env files must be explicitly selected",
    "EnvironmentFile=-@VLOG_ROOT@/.env": "systemd env files must be explicitly selected",
    "ReadWritePaths=@VLOG_ROOT@/data": "the Git checkout must not be mutable runtime state",
    'Path("data/': "mutable runtime paths must resolve through settings/platformdirs",
    "Path('data/": "mutable runtime paths must resolve through settings/platformdirs",
    "open('data/": "mutable runtime paths must resolve through settings/platformdirs",
    'open("data/': "mutable runtime paths must resolve through settings/platformdirs",
    "data/cognee_queue.yaml": "Cognee queue must live under VLOG_STATE_HOME",
    "data/recordings/": "recordings must live under VLOG_DATA_HOME",
    "data/transcripts/": "transcripts must live under VLOG_DATA_HOME",
    "data/summaries/": "summaries must live under VLOG_DATA_HOME",
    "data/novels/": "novels must live under VLOG_DATA_HOME",
    "data/photos/": "photos must live under VLOG_DATA_HOME",
    "data/archives/": "archives must live under VLOG_DATA_HOME",
    "data/skills/": "generated skills must live under VLOG_DATA_HOME",
    "data/heartbeats/": "heartbeats must live under VLOG_STATE_HOME",
    'Path("data/logs")': "service logs must live under VLOG_STATE_HOME",
    "data\\logs\\windows-bootstrap.log": "Windows bootstrap logs must live under VLOG_STATE_HOME",
    "/tmp/vlog-daily.log": "daily logs must live under VLOG_STATE_HOME",
}


def exported_runtime_files() -> list[str]:
    """Enumerate only source-owned runtime files when `.git` is unavailable."""

    files = [relative for relative in RUNTIME_FILES if (ROOT / relative).is_file()]
    for prefix in RUNTIME_PREFIXES:
        directory = ROOT / prefix
        if not directory.is_dir():
            continue
        files.extend(
            path.relative_to(ROOT).as_posix()
            for path in directory.rglob("*")
            if path.is_file()
        )
    return sorted(set(files))


def tracked_files() -> list[str]:
    try:
        raw = subprocess.check_output(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return exported_runtime_files()
    return [item.decode("utf-8") for item in raw.split(b"\0") if item]


def violations(paths: list[str] | None = None) -> list[str]:
    failures: list[str] = []
    for relative in paths or tracked_files():
        if relative == "scripts/check_runtime_contract.py":
            continue
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
