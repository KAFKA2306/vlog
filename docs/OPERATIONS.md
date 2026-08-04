# VLog operations

This runbook covers the current relocated runtime: recording, transcription, generation, synchronization, notifications, systemd supervision, Windows supervision assets, and local incident evidence. Operational logs and raw evidence must not be exposed through the public reader.

The current runtime remains legacy-compatible and file-based. Human Memory v2 migration procedures are documented separately in [`architecture/human-memory-v2.md`](architecture/human-memory-v2.md).

## Completion boundary

Repository validation and environment validation are different:

- `task systemd:verify` proves that rendered unit syntax is valid in the checking environment.
- `task web:build` proves that the Reader can typecheck, lint, and build in the checking environment.
- GitHub Actions does not prove live user-systemd operation, Windows Task Scheduler registration, audio capture, GPU execution, Vercel configuration, Supabase contents, Storage policy, or credentials.

Record environment-specific evidence before reporting an operational cutover as complete.

## Supervision model

The repository contains two supervision layers:

1. Linux/WSL user systemd units under `infra/systemd/` for the monitor and daily pipeline.
2. Windows Task Scheduler and watchdog assets under `infra/windows/` for host-level recovery when WSL or its user manager is unavailable.

The existence and static validation of these assets do not establish that they are installed or functioning on the production host.

Primary machine-local evidence:

- `data/error_events.jsonl`: current structured operational events;
- `data/error_events.jsonl.1` and later generations: rotated events;
- `data/heartbeats/vlog-service.json`: latest monitor heartbeat;
- `data/reports/operations.html`: local operations cockpit;
- `data/reports/operations.json`: machine-readable report;
- systemd journal and Windows watchdog logs.

## Install or update Linux/WSL units

From the repository root:

```bash
git pull --ff-only
task systemd:verify
task systemd:install
```

`infra/systemd/render.py` resolves the active repository root, Python path, and `uv` executable into user-unit files outside the repository. The installer targets `${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user`.

Verify the actual user manager after installation:

```bash
systemctl --user status vlog.service vlog-daily.timer
systemctl --user list-timers vlog-daily.timer --all --no-pager
journalctl --user -u vlog.service -u vlog-daily.service --since "24 hours ago"
```

A host without a working user systemd bus has not completed this cutover, even if template verification succeeds.

## Install or update the Windows watchdog

```powershell
powershell.exe -ExecutionPolicy Bypass -File infra/windows/install-vlog-watchdog.ps1
```

The configured task name is `VLog External Watchdog`; its log is `%LOCALAPPDATA%\VLog\watchdog.log`.

Verify on the actual Windows machine:

- the scheduled task exists and is enabled;
- WSL starts as expected;
- the watchdog detects stale service state;
- the intended service is restarted;
- an actual VRChat session creates a non-empty recording;
- logs identify failures without exposing secrets.

## Incident identity and recovery

Incidents are grouped by `fingerprint + resource_id`. A generic `succeeded` event does not resolve a failure. Resolution requires a `recovered` event that explicitly references the affected fingerprint through `resolves_fingerprint`. A later recurrence reopens the incident.

Example after manual verification:

```bash
uv run python -m src.operations recover-latest \
  --category recording \
  --component audio-recorder \
  --operation start \
  --resource-id audio-input:default \
  --message "Audio input was verified manually"
```

Run Python module commands from the repository root so the Taskfile or environment provides `apps/capture-vrchat` on `PYTHONPATH`.

## Event-log durability

Structured operational events implement:

- inter-process file locking;
- complete-write loops;
- selective `fsync` for failure, recovered, and critical events;
- size and retention controls;
- masking for API keys, tokens, webhooks, and home paths;
- exception type, message, and stack trace;
- service, instance, trace, and span fields.

Configurable environment variables:

```dotenv
VLOG_EVENT_MAX_BYTES=10485760
VLOG_EVENT_BACKUPS=7
VLOG_EVENT_RETENTION_DAYS=90
VLOG_EVENT_FSYNC=failures
```

## Routine diagnosis

```bash
task status
task service:status
task log:status
uv run python -m src.operations doctor --root "$(pwd)"
bash scripts/open_operations.sh 90
cat data/heartbeats/vlog-service.json
```

`task status` invokes both Windows and systemd commands. Use the component-specific commands when one host layer is unavailable.

## Recording checks

The recorder and monitor are expected to surface:

- input stream startup failure or timeout;
- input overflow;
- recorder-thread termination while VRChat remains active;
- stop timeout;
- empty or unexpectedly small recording;
- session processing failure;
- synchronization failure.

Static tests cannot confirm the selected physical audio device, permissions, sample flow, or recording growth. Validate those on the capture host.

## Historical logs

The operations report also reads legacy sources such as `data/incidents.jsonl`, `data/daily_runs.jsonl`, and `data/logs/vlog.log`. Historical classification is compatibility logic; new operational evidence should use the current structured event format. Invalid JSONL rows must remain visible as audit failures rather than being silently skipped.

## systemd failure path

The monitor and daily services use failure units under `infra/systemd/`. A failure handler records unit state and recent journal context locally before sending a brief notification. Detailed logs, evidence, paths, and secrets must not be copied into Discord or the public Reader.

## Verification gate

Repository changes should pass:

```bash
task test
task doc:check
task systemd:verify
task web:build
```

Ruff check and format-check are enforced in CI. Environment changes additionally require evidence from the affected system: Linux/WSL, Windows, Vercel, Supabase, object storage, audio, or GPU.

## Related documents

- [Documentation index](README.md)
- [Maintenance procedures](MAINTENANCE.md)
- [Current runtime architecture](architecture.md)
- [Current daily pipeline contract](daily_pipeline_contract.md)
- [Phase 0 inventory](operations/phase0-inventory.md)
