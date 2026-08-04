# AGENTS.md

VLog is a public OSS engine for capturing VRChat evidence, deriving reviewable memory claims, generating narrative artifacts, and publishing only explicitly approved projections.

## Authority

Use these sources in order:

1. executable schemas, tests, and implementation;
2. [Human Memory v2 architecture](docs/architecture/human-memory-v2.md) for the target state;
3. [current runtime architecture](docs/architecture.md) and component runbooks for existing behavior;
4. [ADR index](docs/adr/README.md) for historical decisions.

The complete documentation map is [docs/README.md](docs/README.md). Agent-specific files must remain short routers and must not duplicate system specifications.

## Repository boundaries

- `apps/`: deployable capture, reader, API, and MCP entry points.
- `packages/`: storage-agnostic domain capabilities.
- `adapters/`: persistence, storage, graph, and vector integrations.
- `infra/`: Supabase, systemd, and Windows assets.
- `schemas/`: versioned interchange contracts.
- `docs/`: architecture, ADRs, operations, and historical incidents.

The runtime is under `apps/capture-vrchat/`; the reader is under `apps/reader/`; operational assets are under `infra/`. Do not recreate retired top-level runtime or infrastructure directories. Do not add private journals, people data, raw evidence, or personal memory to this public repository.

## Data and privacy

- Raw audio, photos, video, full transcripts, and source documents belong in private object storage.
- Reviewed journals, corrections, relationships, preferences, and long-lived memory views belong in the private `kafka-memory` repository.
- AI output is a candidate derived view, not accepted memory or a publication decision.
- Accepted memory claims require provenance to source evidence.
- Graphiti, Cognee, pgvector, and Qdrant are rebuildable projections.
- Structural migrations must not delete or move evidence before Phase 0 inventory and remote exports are complete.

## Change discipline

- Inspect `git status` and the intended diff before staging.
- Never stage unrelated changes with `git add .`.
- Preserve useful comments, docstrings, tests, error context, timeouts, and boundary-specific exception handling.
- Do not change model identifiers without explicit user instruction; read `data/config.yaml` and the implementation first.
- Use repository-relative Markdown links. Do not add user-specific home paths or file-scheme links.
- State separately what is implemented in Git, verified in CI, and verified in the operating environment.

## Verification

Run the checks relevant to the changed boundaries:

```bash
task lint
task test
task doc:check
task systemd:verify
task web:build
```

`task lint` may modify files. Review the resulting diff. GitHub CI does not prove live systemd, Windows Task Scheduler, Vercel, Supabase, private storage, or GPU behavior.
