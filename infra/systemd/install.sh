#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "${BASH_SOURCE[0]%/*}/../.." && pwd)"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
cd "$ROOT"
export VLOG_PROJECT_ROOT="$ROOT"

resolve_executable() {
  local env_name="$1"
  local command_name="$2"
  local candidate="${!env_name:-}"

  if [[ -z "$candidate" ]]; then
    candidate="$(type -P "$command_name" || true)"
  fi
  if [[ -z "$candidate" ]]; then
    echo "$command_name executable was not found; set $env_name to an absolute executable path" >&2
    return 127
  fi
  if [[ "$candidate" != /* ]]; then
    echo "$env_name must resolve to an absolute path: $candidate" >&2
    return 2
  fi
  if [[ ! -x "$candidate" ]]; then
    echo "$command_name executable is not executable: $candidate" >&2
    return 126
  fi
  printf '%s\n' "$candidate"
}

UV_EXE="$(resolve_executable VLOG_UV_EXE uv)"
SYSTEMCTL_EXE="$(resolve_executable VLOG_SYSTEMCTL_EXE systemctl)"
UV_VERSION="$("$UV_EXE" --version 2>&1 || true)"
SYSTEMCTL_VERSION="$("$SYSTEMCTL_EXE" --version 2>&1 || true)"
SYSTEMCTL_VERSION="${SYSTEMCTL_VERSION%%$'\n'*}"

printf 'resolved uv: %s (%s)\n' "$UV_EXE" "$UV_VERSION"
printf 'resolved systemctl: %s (%s)\n' "$SYSTEMCTL_EXE" "$SYSTEMCTL_VERSION"

if [[ "${1:-}" == "--diagnose" ]]; then
  exit 0
fi
if [[ $# -gt 0 ]]; then
  echo "unknown argument: $1" >&2
  exit 2
fi

"$UV_EXE" sync --locked
"$UV_EXE" run --frozen python - <<'PY'
from vlog_capture.portability import runtime_directories

dirs = runtime_directories()
for path in (dirs.config, dirs.data, dirs.state, dirs.cache):
    path.mkdir(parents=True, exist_ok=True)
print(f"config={dirs.config}")
print(f"data={dirs.data}")
print(f"state={dirs.state}")
print(f"cache={dirs.cache}")
PY

"$UV_EXE" run --frozen python infra/systemd/render.py --root "$ROOT" --output "$UNIT_DIR" --uv "$UV_EXE"
"$SYSTEMCTL_EXE" --user daemon-reload
"$SYSTEMCTL_EXE" --user enable --now vlog-daily.timer
"$SYSTEMCTL_EXE" --user enable vlog.service
"$SYSTEMCTL_EXE" --user restart vlog.service

"$UV_EXE" run --frozen vlog-operations doctor --root "$ROOT"
"$UV_EXE" run --frozen vlog-operations recover-latest \
  --category scheduler \
  --component systemd \
  --operation launch \
  --code scheduler_binary_recovered \
  --message "Rendered repository systemd templates and verified the runtime" || true
"$UV_EXE" run --frozen vlog-operations report --days 90 || true

"$SYSTEMCTL_EXE" --user --no-pager status vlog.service || true
echo "Rendered units: $UNIT_DIR"
echo "Operations report is stored under VLOG_STATE_HOME/reports (or the platform default)."
echo "Optional Windows watchdog: powershell.exe -ExecutionPolicy Bypass -File infra/windows/install-vlog-watchdog.ps1"
