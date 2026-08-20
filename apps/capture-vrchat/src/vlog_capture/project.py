from __future__ import annotations

import os
from pathlib import Path


def find_project_root(start: Path | None = None) -> Path:
    """Resolve the repository root without depending on package depth.

    VLOG_PROJECT_ROOT is authoritative when set by an operator. Otherwise the
    nearest ancestor containing pyproject.toml and data/ is used.
    """

    configured = os.environ.get("VLOG_PROJECT_ROOT")
    if configured:
        root = Path(configured).expanduser().resolve()
        if not (root / "pyproject.toml").is_file():
            raise RuntimeError(f"VLOG_PROJECT_ROOT is not a VLog repository: {root}")
        return root

    candidate = (start or Path(__file__)).resolve()
    if candidate.is_file():
        candidate = candidate.parent
    for parent in (candidate, *candidate.parents):
        if (parent / "pyproject.toml").is_file() and (parent / "data").exists():
            return parent
    raise RuntimeError(f"Could not locate VLog repository root from: {candidate}")


PROJECT_ROOT = find_project_root()
