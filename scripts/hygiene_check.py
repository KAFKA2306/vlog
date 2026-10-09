#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from vlog_capture.infrastructure.observability import (
    EventStatus,
    OperationalEventLog,
    Severity,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

AUDIO_SUFFIXES = {".aac", ".flac", ".m4a", ".mp3", ".ogg", ".wav"}
DEFAULT_MIN_BYTES = 100


@dataclass(frozen=True)
class Finding:
    path: Path
    size: int
    reason: str


def _probe_stream(path: Path) -> bool | None:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=codec_name,sample_rate,channels",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            check=False,
            text=True,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return False
    return bool(result.stdout.strip())


def scan(recording_dir: Path, min_bytes: int = DEFAULT_MIN_BYTES) -> list[Finding]:
    findings: list[Finding] = []
    if not recording_dir.is_dir():
        return findings
    for path in sorted(recording_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in AUDIO_SUFFIXES:
            continue
        size = path.stat().st_size
        if size <= min_bytes:
            findings.append(Finding(path, size, "size below minimum"))
            continue
        if _probe_stream(path) is False:
            findings.append(Finding(path, size, "ffprobe found no audio stream"))
    return findings


def _unique_destination(directory: Path, name: str) -> Path:
    destination = directory / name
    index = 1
    while destination.exists():
        destination = directory / f"{name}.{index}"
        index += 1
    return destination


def quarantine(findings: list[Finding], directory: Path, event_log: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    moved: list[Path] = []
    events = OperationalEventLog(event_log)
    for finding in findings:
        destination = _unique_destination(directory, finding.path.name)
        shutil.move(str(finding.path), destination)
        moved.append(destination)
        events.emit(
            category="recording",
            component="hygiene-check",
            operation="quarantine",
            status=EventStatus.SUCCEEDED,
            severity=Severity.WARNING,
            message="Corrupt recording quarantined",
            code="recording_quarantined",
            resource_id=finding.path.name,
            context={
                "size_bytes": finding.size,
                "reason": finding.reason,
                "destination": destination.name,
            },
            source="hygiene-check",
        )
    return moved


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect unusable local recordings")
    parser.add_argument(
        "--recording-dir", type=Path, default=PROJECT_ROOT / "data/recordings"
    )
    parser.add_argument(
        "--quarantine-dir",
        type=Path,
        default=PROJECT_ROOT / "data/archives/quarantine",
    )
    parser.add_argument("--min-bytes", type=int, default=DEFAULT_MIN_BYTES)
    parser.add_argument("--quarantine", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.min_bytes < 0:
        raise SystemExit("--min-bytes must be non-negative")
    findings = scan(args.recording_dir, args.min_bytes)
    if not findings:
        print("Recording hygiene check passed.")
        return 0
    for finding in findings:
        print(f"FOUND {finding.path} ({finding.size} bytes): {finding.reason}")
    if not args.quarantine:
        print("No files moved. Re-run with --quarantine to isolate findings.")
        return 1
    moved = quarantine(
        findings,
        args.quarantine_dir,
        PROJECT_ROOT / "data/error_events.jsonl",
    )
    print(f"Quarantined {len(moved)} recording(s) to {args.quarantine_dir}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
