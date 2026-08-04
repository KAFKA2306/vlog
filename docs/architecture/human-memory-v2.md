# Human Memory Repository v2 Architecture

Status: Phase 0 and Phase 1 boundary establishment

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

- `apps/`: deployable entry points.
- `packages/`: storage-agnostic business capabilities.
- `adapters/`: vendor and persistence implementations.
- `infra/`: systemd, Windows, Supabase migrations, and deployment assets.
- `schemas/`: versioned interchange contracts.
- `docs/`: ADRs, architecture, and operations.

The current `src/` and `frontend/reader/` remain legacy runtime locations during the first migration gate. New domain code must not be added to root `src/domain` unless required to repair production. New Human Memory v2 capabilities go to the target boundary.

## Dependency rule

```text
apps -> packages -> protocols <- adapters
```

Forbidden directions:

- packages importing apps
- domain entities importing Supabase, Graphiti, Cognee, Qdrant, Next.js, or model SDKs
- publication code reading raw private evidence without an explicit authorized use case
- search indexes becoming the only copy of a claim or revision

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

- no raw evidence deletion or relocation;
- generate SHA-256 inventory of legacy local data;
- record Git tracking, byte totals, duplicate hashes, and current commit;
- export Supabase schema, rows, buckets, and RLS separately in the operating environment.

### Gate 1: establish boundaries

- create target directories and versioned schemas;
- add repository boundary checks to CI;
- make AGENTS pointers repository-relative;
- keep current runtime behavior unchanged.

### Gate 2: relocate without behavior change

- move `src` runtime modules into `apps/capture-vrchat` and packages;
- move `frontend/reader` into `apps/reader`;
- move systemd and Windows assets into `infra`;
- update imports, Taskfile, unit paths, tests, and deployment configuration;
- remove legacy locations only after all tests and operating checks pass.

### Gate 3: canonical persistence

- add PostgreSQL migrations for v2 entities, outbox, idempotency, RLS, and publication policy;
- change synchronization from directory scanning to outbox consumers;
- migrate evidence bytes to private storage and retain manifests in Git/private memory views.

## Rollback

Each gate is a separate PR. Git history is the rollback mechanism. Raw evidence is never modified as part of a structural code migration.
