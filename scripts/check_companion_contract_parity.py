from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_CORE = ROOT / "packages" / "companion" / "src" / "vlog_companion" / "core.py"
BROWSER_CORE = ROOT / "apps" / "companion-lab" / "companion-core.mjs"


def extract(text: str, name: str) -> str:
    patterns = (
        rf'^{name}\s*=\s*"([^"]+)"',
        rf"^{name}\s*=\s*([0-9.]+)",
        rf"^export const {name}\s*=\s*'([^']+)'",
        rf"^export const {name}\s*=\s*([0-9.]+)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            return match.group(1)
    raise RuntimeError(f"missing contract constant: {name}")


def main() -> int:
    python_text = PYTHON_CORE.read_text(encoding="utf-8")
    browser_text = BROWSER_CORE.read_text(encoding="utf-8")
    for name in ("KANA", "SLOTS", "WEIGHT_ALPHA", "WEIGHT_BETA", "DECAY_PER_DAY"):
        left = extract(python_text, name)
        right = extract(browser_text, name)
        if left != right:
            raise SystemExit(
                f"companion contract mismatch for {name}: python={left} browser={right}"
            )
    print("Companion Python/browser contract parity passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
