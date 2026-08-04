# Human Memory Repository v2 Architecture

Status: Phase 0 inventory foundation and Phase 1/2 repository boundary relocation implemented

Tracking issue: #14

## System direction

```text
Evidence -> Human Memory -> Narrative Artifact -> Public Projection
```

The pipeline no longer treats a diary, novel, illustration, or AI summary as canonical memory. Generated artifacts are disposable projections that retain references to canonical episodes and claims.

## Canonical stores

| Store | Canonical responsibility |
|---|---|
| Private object storage | raw audio, photo, video, full transcript, and document bytes |
| PostgreSQL/Supabase | source metadata, episodes, utterances, moments, entities, claims, revisions, ingestion runs, outbox, and publication decisions |
| Private `kafka-memory` repository | reviewed journal text, writing policy, long-lived preferences, corrections, and human-maintained memory views |

Graphiti, Cognee, pgvector, and Qdrant are rebuildable projections. They are not authoritative stores.

## Public repository boundaries

- `apps/capture-vrchat/`: current Python capture and processing application. The package remains named `src` during the behavior-preserving migration.
- `apps/reader/`: current Next.js reader and future publication-review surface.
- `apps/api/` and `apps/mcp/`: reserved deployable boundaries.
- `packages/`: storage-agnostic domain and reusable business capabilities.
- `adapters/`: vendor and persistence implementations.
- `infra/`: portable systemd, Windows, and Supabase assets.
- `schemas/`: versioned interchange contracts.
- `docs/`: ADRs, architecture, and operations.

Root-level `src/`, `frontend/`, `windows/`, `supabase/`, and systemd units are rejected by CI so the old layout cannot silently return.

## Dependency rule

```text
apps -> packages -> protocols <- adapters
```

Forbidden directions:

- packages importing applications;
- domain entities importing Supabase, Graphiti, Cognee, Qdrant, Next.js, or model SDKs;
- publication code reading raw private evidence without an explicit authorized use case;
- search indexes becoming the only copy of a claim or revision.

## Executable invariants

The `memory-domain` package enforces:

1. accepted claims require at least one provenance reference;
2. evidence references point to a source object and episode, with an optional utterance/time span;
3. revisions are append-only records of status changes;
4. timestamps are timezone-aware;
5. generated artifacts reference canonical episode or claim IDs;
6. publication requires a separate decision record;
7. ingestion idempotency is keyed by `source_hash + pipeline_version`.

## Migration gates

### Gate 0: freeze and inventory

Implemented in the repository; environment execution remains operator-owned.

- no raw evidence deletion or relocation;
- generate a SHA-256 inventory of local evidence and artifacts;
- record Git tracking, byte totals, duplicate hashes, and current commit;
- export Supabase schema, rows, buckets, object manifests, and RLS in the operating environment.

### Gate 1: establish boundaries

Implemented.

- create target directories and versioned schemas;
- add repository-boundary checks to CI;
- make repository pointers portable;
- keep current runtime behavior unchanged.

### Gate 2: relocate without behavior change

Implemented in the repository layout.

- move the Python runtime from root `src/` to `apps/capture-vrchat/src/`;
- move the Next.js reader from `frontend/reader/` to `apps/reader/`;
- consolidate systemd, Windows, and Supabase assets under `infra/`;
- update import search paths, Taskfile, CI, tests, documentation, and deployment scripts;
- render systemd templates at install time so no repository checkout path is hard-coded in version control;
- keep Cognee as an optional dependency and rebuildable projection.

Operating-system cutover is not inferred from CI. Linux/WSL systemd installation, Windows Task Scheduler, GPU runtime, and live Supabase access require verification in their actual environments.

### Gate 3: canonical persistence

Not yet implemented.

- add PostgreSQL migrations for v2 entities, outbox, idempotency, RLS, and publication policy;
- change synchronization from directory scanning to outbox consumers;
- migrate evidence bytes to private storage and retain manifests in Git/private memory views.

## Rollback

Each gate is a separate PR. Git history is the rollback mechanism. Raw evidence is never modified as part of a structural code migration.
