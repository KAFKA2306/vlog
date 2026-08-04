---
codd:
  node_id: "req:maintenance"
  type: spec
  status: approved
  links:
    - to: Taskfile.yaml
      type: implementation
---

# VLog Maintenance Manual

This document defines repeatable maintenance procedures. Point-in-time service status belongs in operations reports, not in this versioned runbook.

## Routine Verification

```bash
task lint
task test
task doc:check
task systemd:verify
task web:build
```

Environment-specific checks:

```bash
task status
task service:status
task log:status
uv run python -m src.operations doctor --root "$(pwd)"
uv run python -m src.operations report --days 30
```

## systemd

Templates live under `infra/systemd/*.in`. They are rendered into the user systemd directory by `infra/systemd/render.py`; no checkout path is committed in a unit.

```bash
task systemd:verify
task systemd:install
systemctl --user status vlog.service vlog-daily.timer
journalctl --user -u vlog.service -u vlog-daily.service --since "24 hours ago"
```

When a unit fails, inspect the rendered unit, its source template, the journal, `data/error_events.jsonl`, and `data/heartbeats/` before restarting.

## Windows

Canonical scripts live under `infra/windows/`.

```text
infra\windows\bootstrap.bat
infra\windows\run.bat
```

External WSL watchdog:

```powershell
powershell.exe -ExecutionPolicy Bypass -File infra/windows/install-vlog-watchdog.ps1
```

Verify Task Scheduler state, `data/logs/windows-bootstrap.log`, `%LOCALAPPDATA%\VLog\watchdog.log`, and an actual recording created after VRChat starts. WSL-only execution is not Windows verification.

## Evidence and Storage

Before any destructive migration:

```bash
uv run --no-sync python scripts/phase0_inventory.py
```

- Do not delete or relocate raw evidence without a retained inventory and recoverable backup.
- Do not treat a fixed-size Storage listing as complete; paginate until exhaustion.
- Keep raw media in private object storage, not Git.
- Keep publication separate from ingestion and generation.

## Supabase

For schema or policy changes:

1. export the current schema and migration history;
2. record table row counts and key ranges;
3. inventory every bucket with visibility, object count, total bytes, and paginated object manifest;
4. export RLS and Storage policies;
5. apply changes from `infra/supabase/`;
6. verify anonymous, authenticated, and service-role behavior independently.

A connection failure, missing table, or paused project must be reported as an environment condition. Do not mask it by forcing a successful exit.

## Reader

```bash
task web:setup
task web:build
task web:start
```

The application root is `apps/reader/`. A deployment provider configured with the former `frontend/reader` root must be updated during cutover.

## Recovery Order

1. identify the failed component and source evidence;
2. preserve raw inputs and logs;
3. repair configuration or code at its canonical boundary;
4. run focused tests, then the full verification gate;
5. replay only the affected idempotent operation;
6. confirm output, audit event, and downstream visibility;
7. record unresolved environment validation explicitly.
