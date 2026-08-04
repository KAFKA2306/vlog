# VLog documentation

This directory separates the current executable runtime from the Human Memory Repository v2 target architecture.

## Source-of-truth map

| Document | Authority |
|---|---|
| [`../README.md`](../README.md) | repository entry point, setup, and current status |
| [`overview.md`](overview.md) | product purpose, scope, and implementation status |
| [`architecture/human-memory-v2.md`](architecture/human-memory-v2.md) | target architecture, canonical data rules, and migration phases |
| [`architecture.md`](architecture.md) | current file-based runtime and deployable boundaries |
| [`operations/phase0-inventory.md`](operations/phase0-inventory.md) | non-destructive inventory procedure before data migration |
| [`OPERATIONS.md`](OPERATIONS.md) | runtime diagnosis, supervision, incident evidence, and recovery |
| [`MAINTENANCE.md`](MAINTENANCE.md) | repeatable repository and infrastructure maintenance |
| [`daily_pipeline_contract.md`](daily_pipeline_contract.md) | current legacy-compatible daily execution contract |
| [`adr/`](adr/) | accepted design decisions and their rationale |

## Precedence

When documents appear to conflict, use this order:

1. versioned schemas and executable tests;
2. `architecture/human-memory-v2.md` for the target state;
3. a component-specific operations or infrastructure runbook;
4. `architecture.md` and `daily_pipeline_contract.md` for current runtime behavior;
5. historical ADRs and incident reports.

The current runtime intentionally preserves date-named files, directory scans, and Supabase synchronization while migration work continues. Those mechanisms describe existing behavior; they are not the v2 canonical state model.

## Status vocabulary

Documentation uses three distinct states:

- **Implemented in repository**: code, schema, checks, or templates exist and pass repository validation.
- **Environment-verified**: the change has also been executed successfully against the actual host, scheduler, deployment provider, database, or object storage.
- **Planned**: the design is accepted but no production implementation is claimed.

A successful GitHub Actions run does not establish environment verification for systemd, Windows Task Scheduler, Vercel, Supabase contents, private storage, or GPU execution.

## Documentation maintenance rules

- Do not duplicate dependency versions or command lists when `pyproject.toml`, `apps/reader/package.json`, or `Taskfile.yaml` is authoritative.
- Use repository-relative links and paths.
- Mark legacy-compatible behavior explicitly.
- Never describe a migration as complete until both repository validation and the required environment evidence exist.
- Update this index when adding a new normative architecture or operations document.
