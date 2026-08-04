# Current daily pipeline contract

Status: implemented in repository, environment verification required  
Architecture class: legacy-compatible runtime

## Purpose

The daily pipeline advances unprocessed local recordings through the current file-based generation and synchronization flow. It exists to preserve present behavior while Human Memory v2 canonical persistence is being built.

This contract is not the target state model. Date-based filenames, artifact existence checks, directory scans, and the current Supabase synchronization path are scheduled for replacement by stable IDs, explicit ingestion runs, idempotency records, and an outbox in Phase 3.

## Execution contract

| Item | Definition |
|---|---|
| Scheduler | `vlog-daily.timer` starts `vlog-daily.service` |
| Timer source | `infra/systemd/vlog-daily.timer.in` |
| Schedule | 09:00 in the host's configured local timezone; production expects Asia/Tokyo |
| Missed run | `Persistent=true` requests a catch-up after the timer becomes available |
| Entry point | `task process:daily` |
| Preconditions | repository root, `.env`, locked dependencies, required local directories, and any required audio/GPU/network services are available |
| Repository success | the command exits with status 0 and repository validation passes |
| Environment success | the actual service run exits 0, journal evidence exists, and expected outputs and downstream state are verified |
| Failure | a required command exits non-zero and the failure unit records and reports the event |

The timer template currently does not embed an explicit timezone. The production host must therefore be configured for the intended timezone or the template must be changed and revalidated before installation.

## Current processing sequence

1. Inspect VRChat state, resource availability, and pending local work.
2. Avoid heavy processing while VRChat is active.
3. Transcribe eligible recordings.
4. Generate missing summaries, novels, images, and evaluations for dates represented by current files.
5. Process optional projection queues when configured.
6. Synchronize current artifacts to the existing Supabase projection.
7. Emit operational evidence and notifications.

The concrete implementation is authoritative when it differs from this summary. Relevant entry points are `Taskfile.yaml`, `apps/capture-vrchat/src/cli.py`, and `apps/capture-vrchat/src/daily.py`.

## Current data contract

| Input | Current output |
|---|---|
| `data/recordings/` audio | `data/transcripts/` text |
| transcript text | `data/summaries/` summary text |
| summaries | `data/novels/`, `data/photos/`, and evaluation artifacts |
| selected local artifacts | existing Supabase tables and Storage projections |
| runtime operations | structured local events, heartbeats, journal entries, and brief notifications |

Existing outputs may be reused and only missing artifacts generated. That behavior is compatible with the current runtime but does not provide the final v2 guarantees for stable identity, complete provenance, concurrent ingestion, or exact-once outbox delivery.

## Operations

```bash
task systemd:verify
task systemd:install
task status
task logs
task down
```

`task systemd:verify` validates rendered unit syntax. `task systemd:install` modifies the user systemd environment and must be followed by live status and journal checks.

## Completion evidence

Repository evidence:

1. Python compile, Ruff check, and Ruff format-check succeed in CI.
2. `task test` succeeds.
3. `task doc:check` succeeds.
4. `task systemd:verify` succeeds.

Environment evidence:

1. the installed timer shows the intended next trigger time and timezone behavior;
2. `journalctl --user -u vlog-daily.service` records the actual run and exit status;
3. expected pending counts decrease without losing source files;
4. resulting artifacts are non-empty and traceable to their current inputs;
5. Supabase synchronization is verified against live rows, objects, and policy behavior;
6. failure notifications and recovery evidence are tested without exposing private data.

GitHub CI alone cannot satisfy the environment evidence.

## Replacement criteria

This contract can be retired only after Phase 3 and migration reconciliation establish:

- stable UUIDs for source objects, episodes, and artifacts;
- `source_hash + pipeline_version` idempotency;
- explicit ingestion-run state;
- canonical PostgreSQL persistence;
- transactional outbox delivery;
- append-only revisions and provenance;
- complete reconciliation with legacy files and current Supabase data.

## Related documents

- [Current runtime architecture](architecture.md)
- [Human Memory v2 architecture](architecture/human-memory-v2.md)
- [Operations](OPERATIONS.md)
- [Phase 0 inventory](operations/phase0-inventory.md)
