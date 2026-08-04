---
codd:
  node_id: "req:maintenance"
  type: spec
  status: approved
  links:
    - to: Taskfile.yaml
      type: implementation
---

# VLog maintenance manual

This document defines repeatable repository and infrastructure maintenance procedures. Point-in-time service status belongs in generated operations reports, not in this versioned runbook.

## Routine repository verification

Use the commands implemented by `Taskfile.yaml` and CI:

```bash
task test
task doc:check
task systemd:verify
task web:build
```

CI additionally enforces Python compilation, Ruff check, and Ruff format-check. `task lint` currently performs Ruff checking and formatting, so inspect its diff before committing.

Environment-specific diagnosis:

```bash
task status
task service:status
task log:status
uv run python -m src.operations doctor --root "$(pwd)"
uv run python -m src.operations report --days 30
```

A repository check must not be reported as a production-host, Windows, Vercel, Supabase, object-storage, audio, or GPU verification.

## Documentation maintenance

The canonical index is [`README.md`](README.md). When behavior or migration state changes:

1. update executable contracts or schemas first;
2. update the relevant component runbook;
3. update `architecture/human-memory-v2.md` when a migration phase changes state;
4. update `overview.md` and the root README only when the repository-level status changes;
5. run `task doc:check` to validate boundaries and repository-relative links;
6. remove duplicated dependency versions and command lists that can drift from manifest files.

Use the status terms defined in the documentation index: implemented in repository, environment-verified, and planned.

## systemd

Templates live under `infra/systemd/*.in`. `infra/systemd/render.py` writes concrete user units outside the repository; no checkout path is committed in a unit.

```bash
task systemd:verify
task systemd:install
systemctl --user status vlog.service vlog-daily.timer
journalctl --user -u vlog.service -u vlog-daily.service --since "24 hours ago"
```

When a unit fails, inspect the rendered unit, source template, user-manager state, journal, `data/error_events.jsonl`, and `data/heartbeats/` before restarting. A missing user bus is an environment blocker, not a successful installation.

## Windows

Canonical scripts live under `infra/windows/`:

```text
infra\windows\bootstrap.bat
infra\windows\run.bat
infra\windows\register_task.ps1
infra\windows\install-vlog-watchdog.ps1
```

Verify Task Scheduler state, WSL startup, `data/logs/windows-bootstrap.log`, `%LOCALAPPDATA%\VLog\watchdog.log`, watchdog recovery, and an actual recording created after VRChat starts. WSL-only execution is not Windows verification.

## Evidence and storage

Before any destructive migration:

```bash
uv run --no-sync python scripts/phase0_inventory.py
```

Required controls:

- do not delete or relocate raw evidence without a retained inventory and recoverable backup;
- do not treat a fixed-size Storage listing as complete; paginate until exhaustion;
- record hashes, byte totals, object keys, visibility, and source locations;
- keep raw media in private object storage, not Git;
- keep publication separate from ingestion and generation;
- reconcile every migrated source before deleting a legacy copy.

Follow [`operations/phase0-inventory.md`](operations/phase0-inventory.md) for the inventory procedure.

## Supabase

For schema, row, RLS, or Storage-policy changes:

1. export current schema and migration history;
2. record table row counts, key ranges, and required checksums;
3. inventory every bucket with visibility, object count, total bytes, and a complete paginated manifest;
4. export RLS and Storage policies;
5. apply versioned changes from `infra/supabase/`;
6. verify anonymous, authenticated, and service-role behavior independently;
7. reconcile the result with the retained pre-change exports.

A connection failure, missing table, paused project, partial object listing, or unavailable credential is an environment condition. Do not force a successful exit or infer completion.

## Reader

```bash
task web:setup
task web:build
task web:start
```

The application root is `apps/reader/`. A Vercel project configured with the former `frontend/reader` root has not completed the cutover. Verify the provider configuration and deployed revision, not only the local build.

## Human Memory v2 phase changes

Before advancing a phase in documentation or Issue #14:

- identify which acceptance conditions are repository-only and which require live evidence;
- record the commit or PR implementing the repository change;
- retain inventory, export, migration, and reconciliation artifacts outside public Git when they contain private data;
- keep legacy behavior until the replacement has been reconciled;
- do not combine raw-data movement with an unrelated structural refactor;
- document rollback separately for code and data.

## Recovery order

1. identify the failed component and preserve source evidence;
2. preserve logs, manifests, current state, and relevant hashes;
3. repair configuration or code at its canonical boundary;
4. run focused tests, then repository verification;
5. replay only the affected idempotent operation;
6. confirm output, operational evidence, and downstream visibility;
7. reconcile the repaired state with its source;
8. record unresolved environment validation explicitly.

## Related documents

- [Documentation index](README.md)
- [Operations](OPERATIONS.md)
- [Current runtime architecture](architecture.md)
- [Human Memory v2 architecture](architecture/human-memory-v2.md)
- [Current daily pipeline contract](daily_pipeline_contract.md)
