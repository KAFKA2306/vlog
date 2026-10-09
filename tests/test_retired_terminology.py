from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_retired_compatibility_term_does_not_return() -> None:
    result = subprocess.run(
        ["git", "grep", "-I", "-i", "-l", "--", "lega" + "cy"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode in {0, 1}
    assert result.stdout.splitlines() == []
