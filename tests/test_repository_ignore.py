import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

IGNORED = [
    "data/asset_manifest.sqlite",
    "frontend/reader/node_modules/pkg/index.js",
    "frontend/reader/.next/cache/chunk.js",
    "frontend/reader/next-env.d.ts",
    "frontend/reader/tsconfig.tsbuildinfo",
    "apps/reader/node_modules/pkg/index.js",
    "colleague-skill/README.md",
    ".serena/project.yml",
    "codd/scan/nodes.jsonl",
    ".codd/scan/edges.jsonl",
    "vendor/libvips.so.8.17.3",
    "vendor/native.node",
    "vendor/index.sst",
    ".env",
]

TRACKED = [
    "config/mochio.yaml",
    "Taskfile.yaml",
    "scripts/asset_manifest.py",
    "pyproject.toml",
    "docs/OPERATIONS.md",
    ".gitignore",
]


def _ignored(path: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "check-ignore", "--no-index", "-q", path],
        check=False,
    )
    return result.returncode == 0


@pytest.mark.parametrize("path", IGNORED)
def test_generated_and_local_paths_are_ignored(path: str) -> None:
    assert _ignored(path), f"{path} must be ignored"


@pytest.mark.parametrize("path", TRACKED)
def test_source_and_config_paths_are_not_ignored(path: str) -> None:
    assert not _ignored(path), f"{path} must stay trackable"
