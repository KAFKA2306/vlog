---
name: windows-cmd-ps1-ops
description: Windows operations protocol for running and recovering VLog through Task Scheduler, `run.bat`, `bootstrap.bat`, and the external WSL watchdog. Trigger for UNC launch failures, uv/Python resolution, ExecutionPolicy blockers, restart loops, or Windows-side logging.
---

# Windows CMD/PS1 Ops

## 1. Responsibility Split
- `infra/windows/bootstrap.bat` prepares the Windows environment and registers the logon task.
- `infra/windows/run.bat` resolves the repository root, sets `PYTHONPATH`, and starts `python -m src.main`.
- `infra/windows/install-vlog-watchdog.ps1` registers the external WSL watchdog.
- `infra/windows/vlog-watchdog.ps1` probes systemd and heartbeat state, then requests recovery when stale.

## 2. Path and Toolchain Normalization
- Derive the repository root from each script location; do not hard-code a user home path.
- Use `pushd` for UNC paths.
- Use `.venv-win`, Python 3.12, and `uv sync --frozen`.

## 3. Recovery Rules
- Prevent duplicate scheduled-task instances.
- Record the resolved project path before launch.
- Restart only after the service/heartbeat probe proves the runtime unhealthy.

## 4. Logging Rules
- Keep `timestamp`, `resolved_path`, `working_dir`, and `exit_code` explicit.
- Store Windows bootstrap logs under `data/logs/` and external watchdog logs under `%LOCALAPPDATA%\\VLog`.

## 5. Definition of Done
- `VlogAutoDiary` remains running after launch.
- VRChat detection creates evidence in `data/recordings/`.
- systemd heartbeat and external watchdog recovery are observable.
- No script depends on `/home/kafka/...` or another fixed checkout path.
