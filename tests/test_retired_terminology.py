from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_retired_compatibility_term_does_not_return() -> None:
    needle = ("lega" + "cy").encode()
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).split(b"\0")
    matches: list[str] = []
    for raw in tracked:
        if not raw:
            continue
        relative = raw.decode("utf-8")
        path = ROOT / relative
        if not path.is_file():
            continue
        try:
            content = path.read_bytes().lower()
        except OSError:
            continue
        if needle in content:
            matches.append(relative)
    assert matches == []
