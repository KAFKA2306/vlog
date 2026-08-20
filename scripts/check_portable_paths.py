#!/usr/bin/env python3
"""Reject tracked paths that cannot be represented safely on Windows and POSIX."""

from __future__ import annotations

import argparse
import subprocess
from collections.abc import Iterable

INVALID_WINDOWS_CHARS = set('<>:"\\|?*')
RESERVED_WINDOWS_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "CLOCK$",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def path_violations(path: str) -> list[str]:
    violations: list[str] = []
    for component in path.split("/"):
        if not component:
            violations.append("empty path component")
            continue
        if component.endswith((" ", ".")):
            violations.append(f"trailing dot/space: {component!r}")
        bad = sorted(set(component) & INVALID_WINDOWS_CHARS)
        if bad:
            violations.append(
                f"Windows-invalid character(s) {''.join(bad)!r}: {component!r}"
            )
        stem = component.split(".", 1)[0].upper()
        if stem in RESERVED_WINDOWS_NAMES:
            violations.append(f"Windows reserved device name: {component!r}")
        if component.casefold().endswith(":zone.identifier"):
            violations.append(
                "Windows alternate-data-stream metadata was materialized as a filename"
            )
    return violations


def validate_paths(paths: Iterable[str]) -> dict[str, list[str]]:
    failures: dict[str, list[str]] = {}
    folded_prefixes: dict[str, tuple[str, str]] = {}
    for path in paths:
        reasons = path_violations(path)
        parts = path.split("/")
        for index in range(len(parts)):
            prefix = "/".join(parts[: index + 1])
            key = prefix.casefold()
            previous = folded_prefixes.get(key)
            if previous is not None and previous[0] != prefix:
                previous_prefix, previous_path = previous
                reasons.append(
                    f"case-fold collision at {prefix!r} with {previous_prefix!r}"
                )
                failures.setdefault(previous_path, []).append(
                    f"case-fold collision with {prefix!r}"
                )
            else:
                folded_prefixes[key] = (prefix, path)
        if reasons:
            failures.setdefault(path, []).extend(reasons)
    return failures


def tracked_paths() -> list[str]:
    output = subprocess.check_output(["git", "ls-files", "-z"])
    return [
        item.decode("utf-8", "surrogateescape") for item in output.split(b"\0") if item
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()
    failures = validate_paths(args.paths or tracked_paths())
    if not failures:
        print("portable-path-check: PASS")
        return 0
    for path, reasons in sorted(failures.items()):
        for reason in reasons:
            print(f"portable-path-check: FAIL: {path}: {reason}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
