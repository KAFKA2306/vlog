#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
cd "$ROOT"
export VLOG_PROJECT_ROOT="$ROOT"

uv sync --locked
uv run --frozen python - <<'PY'
from vlog_capture.portability import runtime_directories

dirs = runtime_directories()
for path in (dirs.config, dirs.data, dirs.state, dirs.cache):
    path.mkdir(parents=True, exist_ok=True)
print(f"config={dirs.config}")
print(f"data={dirs.data}")
print(f"state={dirs.state}")
print(f"cache={dirs.cache}")
PY

uv run --frozen python infra/systemd/render.py --root "$ROOT" --output "$UNIT_DIR"
systemctl --user daemon-reload
systemctl --user enable --now vlog-daily.timer
systemctl --user enable vlog.service
systemctl --user restart vlog.service

uv run --frozen vlog-operations doctor --root "$ROOT"
uv run --frozen vlog-operations recover-latest \
  --category scheduler \
  --component systemd \
  --operation launch \
  --code scheduler_binary_recovered \
  --message "Rendered repository systemd templates and verified the runtime" || true
uv run --frozen vlog-operations report --days 90 || true

systemctl --user --no-pager status vlog.service || true
echo "Rendered units: $UNIT_DIR"
echo "Operations report is stored under VLOG_STATE_HOME/reports (or the platform default)."
echo "Optional Windows watchdog: powershell.exe -ExecutionPolicy Bypass -File infra/windows/install-vlog-watchdog.ps1"
