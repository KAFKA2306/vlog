#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PATHS = (
    "apps",
    "apps/capture-vrchat",
    "apps/reader",
    "packages",
    "packages/memory-domain",
    "packages/ingestion",
    "adapters",
    "infra",
    "infra/systemd",
    "infra/windows",
    "infra/supabase",
    "schemas",
    "docs/architecture",
    "docs/operations",
)
PRIVATE_ROOTS = (
    "journal/",
    "memory/people/",
    "memory/relationships/",
    "memory/self/",
    "feedback/",
    "sources/",
)
RAW_MEDIA_SUFFIXES = {
    ".wav",
    ".flac",
    ".mp3",
    ".m4a",
    ".aac",
    ".ogg",
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
}
NON_PORTABLE_MARKDOWN_LINKS = (
    re.compile(r"\]\(file://[^)]*\)"),
    re.compile(r"\]\(/home/[^)]*\)"),
    re.compile(r"\]\([A-Za-z]:\\[^)]*\)"),
)
LEGACY_PATHS = (
    "src",
    "frontend",
    "windows",
    "supabase",
    "vlog.service",
    "vlog-monitor-failure.service",
    "vlog-daily.service",
    "vlog-daily.timer",
    "vlog-daily-failure.service",
)
MAX_GIT_FILE_BYTES = 100 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class Violation:
    code: str
    path: str
    message: str


def tracked_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    return sorted(
        item.decode("utf-8", errors="surrogateescape")
        for item in result.stdout.split(b"\0")
        if item
    )


def check(root: Path) -> list[Violation]:
    violations: list[Violation] = []
    tracked = tracked_files(root)

    for legacy in LEGACY_PATHS:
        if (root / legacy).exists():
            violations.append(
                Violation("legacy-boundary", legacy, "legacy root must remain removed"),
            )

    for required in REQUIRED_PATHS:
        if not (root / required).exists():
            violations.append(
                Violation(
                    "missing-boundary", required, "required v2 boundary is absent"
                ),
            )

    for relative in tracked:
        path = root / relative
        if path.suffix.lower() == ".md" and path.is_file():
            text = path.read_text(encoding="utf-8")
            for pattern in NON_PORTABLE_MARKDOWN_LINKS:
                match = pattern.search(text)
                if match:
                    violations.append(
                        Violation(
                            "non-portable-markdown-pointer",
                            relative,
                            f"contains non-portable Markdown link: {match.group(0)}",
                        ),
                    )

        normalized = relative.replace("\\", "/")
        if any(normalized.startswith(prefix) for prefix in PRIVATE_ROOTS):
            violations.append(
                Violation(
                    "private-memory-in-public-repo",
                    relative,
                    "private memory belongs in kafka-memory, not vlog",
                ),
            )
        if path.suffix.lower() in RAW_MEDIA_SUFFIXES:
            violations.append(
                Violation(
                    "raw-media-tracked",
                    relative,
                    "raw audio/video must be stored in private object storage",
                ),
            )
        if (
            path.is_file()
            and not path.is_symlink()
            and path.stat().st_size > MAX_GIT_FILE_BYTES
        ):
            violations.append(
                Violation(
                    "oversized-git-object",
                    relative,
                    "tracked file exceeds GitHub's 100 MiB file limit",
                ),
            )

    return violations


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Human Memory v2 boundaries.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.expanduser().resolve()
    violations = check(root)
    if not violations:
        print("Repository boundary check passed.")
        return 0

    for violation in violations:
        print(
            f"{violation.code}: {violation.path}: {violation.message}",
            file=sys.stderr,
        )
    print(
        f"Boundary check failed with {len(violations)} violation(s).", file=sys.stderr
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
