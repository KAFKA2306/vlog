# AGENTS.md

VLog is a public OSS engine for capturing VRChat Evidence, deriving reviewable memory claims, generating narrative artifacts, and publishing only explicitly approved projections.

## Authority

Use these sources in order:

1. executable schemas, tests, package manifests, `Taskfile.yaml`, and implementation;
2. [product specification and guarantees](docs/SPEC.md);
3. [Human Memory v2 architecture](docs/architecture/human-memory-v2.md) for target state;
4. [current runtime architecture](docs/architecture.md) and component runbooks for existing behavior;
5. [ADR index](docs/adr/README.md) for decision rationale.

The complete documentation map is [docs/README.md](docs/README.md). Agent-specific files are routers, not parallel specifications.

## Repository boundaries

- `apps/`: deployable applications and runtime entry points.
- `packages/`: storage-agnostic domain capabilities.
- `adapters/`: persistence, storage, graph, and external integrations.
- `infra/`: Supabase, systemd, and Windows assets.
- `schemas/`: versioned interchange contracts.
- `docs/`: specification, architecture, operations, and decisions.

Capture runtime is the installable `vlog_capture` package. Use manifest-defined console entry points; do not reintroduce runtime `PYTHONPATH`, `python -m src...`, or retired top-level runtime directories.

## Data and privacy

- Raw Evidence and private memory belong in private storage, not this public repository.
- AI output is a candidate derived view, not accepted memory or a publication decision.
- Accepted claims require provenance to source Evidence.
- Graph/vector systems are rebuildable projections, never canonical memory.
- Structural migration must not move or delete Evidence before inventory, backup, and reconciliation.

## Change discipline

- Inspect current implementation before changing a contract.
- Update one existing authority instead of creating parallel specifications or aliases.
- Prefer fewer entry points: `vlog` for product operations, `vlog-operations` for operational diagnosis, `task` for repository orchestration.
- Do not duplicate versions, requirements, task inventories, model IDs, or volatile service status in Markdown.
- Preserve useful tests, error context, timeouts, and boundary-specific exception handling.
- Separate repository/CI verification from actual environment verification.

## Branch lifecycle

- `main` and same-repository head branches of open pull requests are the only remote branches allowed to persist.
- Create a remote work branch only as part of immediately opening its pull request.
- When a pull request is merged or closed, its same-repository head branch must be deleted.
- `.github/workflows/branch-lifecycle.yml` is the executable enforcement authority.

## Verification

Run the canonical repository gate:

```bash
task verify
```

Use focused tasks while iterating. `task lint` is read-only; `task format` modifies Python files. CI does not prove live systemd, Windows Task Scheduler, Vercel, Supabase, private storage, audio, or GPU behavior.
