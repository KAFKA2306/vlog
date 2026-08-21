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

- `apps/`: deployable capture, reader, API, and MCP entry points.
- `packages/`: storage-agnostic domain capabilities.
- `adapters/`: persistence, storage, graph, and external integrations.
- `infra/`: Supabase, systemd, and Windows assets.
- `schemas/`: versioned interchange contracts.
- `docs/`: specification, architecture, contracts, ADRs, operations, and incidents.

Capture runtime is the installable `vlog_capture` package under `apps/capture-vrchat/`. Use the manifest-defined `vlog`, `vlog-service`, `vlog-daily`, and `vlog-operations` console entry points. Do not reintroduce runtime `PYTHONPATH`, `python -m src...`, or retired top-level runtime/infrastructure directories.

## Data and privacy

- Raw audio, photos, video, full transcripts, and source documents belong in private storage.
- Reviewed journals, corrections, relationships, preferences, and long-lived personal memory views do not belong in this public repository.
- AI output is a candidate derived view, not accepted memory or a publication decision.
- Accepted memory claims require provenance to source Evidence.
- Graph/vector systems are rebuildable projections, not canonical memory.
- Structural migration must not delete or move Evidence before inventory, backup, and reconciliation.

## Change discipline

- Inspect current implementation and the intended diff before modifying a contract.
- Update the existing authority instead of creating another Markdown specification.
- Do not duplicate dependency versions, Python requirements, task inventories, model IDs, or temporary service status in docs.
- Use repository-relative Markdown links and portable paths.
- Separate implemented-in-repository, CI-verified, and environment-verified claims.
- Do not change model identifiers without explicit user instruction; inspect current configuration and consuming code first.
- Preserve useful tests, error context, timeouts, and boundary-specific exception handling.

## Branch lifecycle

- `main` and same-repository head branches of open pull requests are the only remote branches allowed to persist.
- Create a remote work branch only as part of immediately opening its pull request.
- When a pull request is merged or closed, its same-repository head branch must be deleted.
- `.github/workflows/branch-lifecycle.yml` is the executable enforcement authority.

## Verification

Run checks relevant to the changed boundaries:

```bash
task lint
task test
task doc:check
task systemd:verify
task web:build
```

`task lint` may modify files, so review its diff. GitHub CI does not prove live systemd, Windows Task Scheduler, Vercel, Supabase, private storage, audio, or GPU behavior.
