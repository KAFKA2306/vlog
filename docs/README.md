# VLog documentation

This directory separates current executable behavior, target architecture, operations, decisions, and historical evidence.

## Source-of-truth map

| Document | Authority |
|---|---|
| [`../README.md`](../README.md) | repository entry point, setup, and current migration status |
| [`overview.md`](overview.md) | product purpose and scope |
| [`architecture/human-memory-v2.md`](architecture/human-memory-v2.md) | target architecture, canonical stores, and migration phases |
| [`architecture.md`](architecture.md) | current file-based runtime and deployable boundaries |
| [`daily_pipeline_contract.md`](daily_pipeline_contract.md) | current legacy-compatible scheduled execution contract |
| [`OPERATIONS.md`](OPERATIONS.md) | diagnosis, supervision, incident evidence, and recovery |
| [`MAINTENANCE.md`](MAINTENANCE.md) | repeatable repository and infrastructure maintenance |
| [`operations/phase0-inventory.md`](operations/phase0-inventory.md) | non-destructive inventory before data migration |
| [`image.md`](image.md) | current illustration-generation boundary |
| [`adr/README.md`](adr/README.md) | architecture decision index and status |
| [`incidents/`](incidents/) | dated historical incident records, not current status |
| [`markdown-governance.md`](markdown-governance.md) | Markdown ownership, retention, and validation rules |

## Precedence

When documents conflict, use this order:

1. schemas, tests, package manifests, Taskfile, and implementation;
2. target architecture for intended state;
3. component-specific runbooks for current operation;
4. current runtime architecture and pipeline contract;
5. ADRs for decision rationale;
6. historical incidents and archived observations.

## Status vocabulary

- **Implemented in repository**: code, schema, tests, or templates exist.
- **CI-verified**: repository checks passed for a specific commit.
- **Environment-verified**: the actual host, deployment, database, storage, network, or GPU behavior was observed.
- **Historical**: true only for the dated evidence and environment recorded.
- **Planned**: accepted direction without a production implementation claim.

CI does not establish environment verification.

## Maintenance rules

- Update an existing authority instead of creating a parallel specification.
- Link to volatile configuration and code instead of copying dependency versions, task inventories, model names, or implementation symbols.
- Use repository-relative links and redact personal paths.
- Put point-in-time service observations under `incidents/`, not in normative runbooks.
- Keep agent files as concise routers.
- Run `task doc:check`.
