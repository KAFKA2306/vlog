#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

for unit in \
  vlog.service \
  vlog-monitor-failure.service \
  vlog-daily.service \
  vlog-daily.timer \
  vlog-daily-failure.service
do
  systemctl --user link --force "$ROOT/$unit"
done

systemctl --user daemon-reload
systemctl --user enable --now vlog-daily.timer
systemctl --user restart vlog.service

uv run python -m src.operations doctor --root "$ROOT"
uv run python -m src.operations report --days 90

echo "Operations report: $ROOT/data/reports/operations.html"
