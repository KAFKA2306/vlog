from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def _repository_root() -> Path:
    configured = os.environ.get("VLOG_PROJECT_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path.cwd().resolve()


def ingest(
    *,
    run_id: str | None = None,
    source_root: str | None = None,
    private_root: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    repository = _repository_root()
    from vlog_vrcpet.runner import run_ingest

    if source_root is not None:
        os.environ["VLOG_VRCPET_ROOT"] = source_root
    if private_root is not None:
        os.environ["VLOG_PRIVATE_EVIDENCE_ROOT"] = private_root
    summary = run_ingest(
        project_root=repository,
        run_id=run_id,
        dry_run=dry_run,
    )
    return summary.as_dict()
