#!/usr/bin/env python3
"""Write apps/reader/.env.local from already-authorized process environment values."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "apps" / "reader" / ".env.local"
REQUIRED = ("NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_ANON_KEY")


def quote_dotenv(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )
    return f'"{escaped}"'


def render(values: dict[str, str]) -> str:
    missing = [name for name in REQUIRED if not values.get(name)]
    if missing:
        raise ValueError("missing environment variable(s): " + ", ".join(missing))
    return "".join(f"{name}={quote_dotenv(values[name])}\n" for name in REQUIRED)


def main() -> int:
    try:
        content = render(dict(os.environ))
    except ValueError as exc:
        print(f"write-reader-env: FAIL: {exc}", file=sys.stderr)
        return 1
    TARGET.write_text(content, encoding="utf-8")
    print(f"wrote {TARGET} from process environment; no dotenv file was sourced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
