#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

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
    "docs/adr/README.md",
    "docs/markdown-governance.md",
)
PRIVATE_ROOTS = (
    "journal/",
    "memory/people/",
    "memory/relationships/",
    "memory/self/",
    "feedback/",
    "sources/",
)
PUBLIC_DATA_FILES = {
    "data/config.yaml",
    "data/prompts.yaml",
}
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
LEGACY_PATHS = (
    ".codd",
    ".codd_version",
    "src",
    "frontend",
    "windows",
    "supabase",
    "codd",
    "bootstrap.bat",
    "run.bat",
    "vlog.service",
    "vlog-monitor-failure.service",
    "vlog-daily.service",
    "vlog-daily.timer",
    "vlog-daily-failure.service",
    "apps/capture-vrchat/src/vlog_capture/infrastructure/audit.py",
)
RETIRED_MARKDOWN = {
    "docs/DAILY_MONITORING.md",
    "docs/logs/20260220_crash_analysis.md",
    "docs/requirements/requirements.md",
}
NON_PORTABLE_TEXT = (
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"/home/[A-Za-z0-9_.-]+/"),
    re.compile(r"[A-Za-z]:\\\\"),
)
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
H1 = re.compile(r"^#\s+\S", re.MULTILINE)
CODD_FRONTMATTER = re.compile(
    r"\A---\s*\n.*?^codd:\s*$.*?^---\s*$", re.MULTILINE | re.DOTALL
)
MAX_GIT_FILE_BYTES = 100 * 1024 * 1024
MAX_AGENT_MARKDOWN_LINES = 180


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


def _strip_code_fences(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def _local_link_failure(root: Path, source: Path, raw_target: str) -> str | None:
    target = raw_target.strip()
    if not target or target.startswith(("http://", "https://", "mailto:", "tel:", "#")):
        return None
    target = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    if not target:
        return None
    candidate = (source.parent / target).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return f"link escapes repository: {raw_target}"
    if not candidate.exists():
        return f"link target is missing: {raw_target}"
    return None


def check_markdown(root: Path, tracked: list[str]) -> list[Violation]:
    violations: list[Violation] = []
    for relative in tracked:
        path = root / relative
        if path.suffix.lower() not in {".md", ".markdown"} or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if relative != "GEMINI.md" and not H1.search(text):
            violations.append(
                Violation(
                    "markdown-missing-h1",
                    relative,
                    "retained Markdown requires an H1 heading",
                )
            )
        if CODD_FRONTMATTER.search(text):
            violations.append(
                Violation(
                    "retired-codd-metadata",
                    relative,
                    "CoDD front matter must remain removed",
                )
            )
        for pattern in NON_PORTABLE_TEXT:
            match = pattern.search(text)
            if match:
                violations.append(
                    Violation(
                        "non-portable-markdown",
                        relative,
                        f"contains non-portable path text: {match.group(0)}",
                    )
                )
        for raw_target in MARKDOWN_LINK.findall(_strip_code_fences(text)):
            failure = _local_link_failure(root, path, raw_target)
            if failure:
                violations.append(Violation("broken-markdown-link", relative, failure))
        if relative.startswith((".agent/", ".claude/", ".gemini/")):
            line_count = len(text.splitlines())
            if line_count > MAX_AGENT_MARKDOWN_LINES:
                violations.append(
                    Violation(
                        "oversized-agent-doc",
                        relative,
                        f"agent Markdown has {line_count} lines; route to canonical docs instead",
                    )
                )
    for retired in sorted(RETIRED_MARKDOWN):
        if retired in tracked:
            violations.append(
                Violation(
                    "retired-markdown", retired, "retired document must not return"
                )
            )
    return violations


def check(root: Path) -> list[Violation]:
    violations: list[Violation] = []
    tracked = tracked_files(root)

    for legacy in LEGACY_PATHS:
        if (root / legacy).exists():
            violations.append(
                Violation("legacy-boundary", legacy, "legacy path must remain removed")
            )
    if "codd-dev" in (root / "pyproject.toml").read_text(encoding="utf-8"):
        violations.append(
            Violation(
                "retired-codd-dependency",
                "pyproject.toml",
                "CoDD is not part of the repository verification toolchain",
            )
        )
    for required in REQUIRED_PATHS:
        if not (root / required).exists():
            violations.append(
                Violation(
                    "missing-boundary", required, "required v2 boundary is absent"
                )
            )

    violations.extend(check_markdown(root, tracked))

    for relative in tracked:
        path = root / relative
        normalized = relative.replace("\\", "/")
        if any(normalized.startswith(prefix) for prefix in PRIVATE_ROOTS):
            violations.append(
                Violation(
                    "private-memory-in-public-repo",
                    relative,
                    "private memory belongs in kafka-memory, not vlog",
                )
            )
        if normalized.startswith("data/") and normalized not in PUBLIC_DATA_FILES:
            violations.append(
                Violation(
                    "noncanonical-data-file",
                    relative,
                    "public repository data/ is limited to versioned config and prompts",
                )
            )
        if path.suffix.lower() in RAW_MEDIA_SUFFIXES:
            violations.append(
                Violation(
                    "raw-media-tracked",
                    relative,
                    "raw audio/video must be stored in private object storage",
                )
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
                )
            )
    return violations


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Human Memory v2 repository and Markdown boundaries."
    )
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.expanduser().resolve()
    violations = check(root)
    if not violations:
        print("Repository and Markdown boundary check passed.")
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
