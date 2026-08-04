#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
cd "$ROOT"
export VLOG_PROJECT_ROOT="$ROOT"
export PYTHONPATH="$ROOT/apps/capture-vrchat:$ROOT/packages/memory-domain/src:$ROOT/packages/ingestion/src${PYTHONPATH:+:$PYTHONPATH}"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

python3 infra/systemd/render.py --root "$ROOT" --output "$UNIT_DIR"
systemctl --user daemon-reload
systemctl --user enable --now vlog-daily.timer
systemctl --user enable vlog.service
systemctl --user restart vlog.service

uv run python -m src.operations doctor --root "$ROOT"
uv run python -m src.operations recover-latest \
  --category scheduler \
  --component systemd \
  --operation launch \
  --code scheduler_binary_recovered \
  --message "Rendered repository systemd templates and verified the runtime" || true
uv run python -m src.operations report --days 90 || true

systemctl --user --no-pager status vlog.service || true
echo "Rendered units: $UNIT_DIR"
echo "Operations report: $ROOT/data/reports/operations.html"
echo "Optional Windows watchdog: powershell.exe -ExecutionPolicy Bypass -File infra/windows/install-vlog-watchdog.ps1"
