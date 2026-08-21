#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DAYS="${1:-90}"
uv run --frozen vlog-operations report --days "$DAYS" --open
