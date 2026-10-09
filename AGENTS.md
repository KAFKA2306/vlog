# AGENTS.md

VLog is a public OSS engine: Evidence -> reviewable memory -> narrative artifacts -> explicitly approved public projections.

## Authority

Use, in order:

1. implementation, tests, schemas, package manifests, and `Taskfile.yaml`;
2. [product specification](docs/SPEC.md);
3. [Human Memory v2 target](docs/architecture/human-memory-v2.md);
4. [current runtime](docs/architecture.md) and runbooks;
5. [ADRs](docs/adr/README.md).

Use [docs/README.md](docs/README.md) as the documentation map. Agent-specific files are routers only.

## Invariants

- Public repository contains no raw Evidence, private memory, credentials, or unapproved publication state.
- AI output is derived/candidate data. Accepted claims require source provenance.
- Graph/vector systems are rebuildable projections, not canonical memory.
- Do not move or delete Evidence during structural migration until inventory, backup, and reconciliation complete.
- Runtime is the installable `vlog_capture` package; do not restore `PYTHONPATH`, `python -m src...`, or retired top-level runtime trees.
- Prefer existing authorities over new aliases/specs; do not duplicate versions, commands, model IDs, requirements, or volatile status.
- Entry points: `vlog` for product operations, `vlog-operations` for diagnosis, `task` for repository orchestration.
- Preserve useful tests, timeouts, error context, and boundary-specific exception handling.
- Repository/CI verification does not prove live host or service state.

## Change workflow

- Inspect current implementation before changing a contract.
- Keep remote branches to `main` and same-repository open-PR heads; `.github/workflows/branch-lifecycle.yml` enforces cleanup.
- Run `task verify`. Use focused tasks while iterating; `task lint` is read-only and `task format` mutates Python.
