#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/apps/capture-vrchat:$ROOT/packages/memory-domain/src:$ROOT/packages/ingestion/src${PYTHONPATH:+:$PYTHONPATH}"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

DAYS="${1:-90}"
uv run python -m src.operations report --days "$DAYS" --open
