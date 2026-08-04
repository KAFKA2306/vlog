# Human Memory Repository v2 architecture

Status date: 2026-08-04  
Tracking issue: [#14](https://github.com/KAFKA2306/vlog/issues/14)

## Status summary

The public repository foundation and behavior-preserving runtime relocation are implemented. The production data inventory, environment cutover, private memory repository, canonical persistence, storage migration, retrieval, and legacy removal remain incomplete.

| Phase | Repository status | Environment status |
|---|---|---|
| 0. Freeze and inventory | inventory tooling and boundary checks implemented | production inventory and Supabase/storage export pending |
| 1. Public repository boundaries | completed by PRs [#15](https://github.com/KAFKA2306/vlog/pull/15) and [#16](https://github.com/KAFKA2306/vlog/pull/16) | systemd, Windows, Vercel, and live Supabase cutover pending |
| 2. Private memory repository | not implemented | not started |
| 3. Canonical memory model | domain models and provenance invariant implemented | migrations, UUID migration, outbox, and canonical persistence pending |
| 4. Storage migration | not implemented | not started |
| 5. Retrieval and MCP | application boundaries reserved | not started |
| 6. Legacy removal | not implemented | blocked on full reconciliation |

“Implemented in repository” means code, schemas, tests, or templates exist. It does not mean the change has run successfully against the production host, scheduler, database, storage, deployment provider, or GPU.

## System direction

```text
Evidence -> Human Memory -> Narrative Artifact -> Public Projection
```

The system must not treat a diary, novel, illustration, AI summary, graph, or vector index as canonical memory. Generated artifacts are rebuildable views that retain references to canonical episodes and claims.

## Target canonical stores

| Store | Canonical responsibility |
|---|---|
| Private object storage | raw audio, photos, video, full transcripts, documents, and other evidence bytes |
| PostgreSQL/Supabase | source metadata, episodes, utterances, moments, entities, claims, revisions, ingestion runs, idempotency state, outbox events, and publication decisions |
| Private `kafka-memory` repository | reviewed journal text, writing policy, long-lived preferences, corrections, and human-maintained memory views |

Graphiti, Cognee, pgvector, and Qdrant are rebuildable projections. They are not authoritative stores.

## Public repository boundaries

- `apps/capture-vrchat/`: current Python capture and processing application. The package remains named `src` during the behavior-preserving migration.
- `apps/reader/`: current Next.js reader and future review/publication surface.
- `apps/api/` and `apps/mcp/`: reserved deployable boundaries.
- `packages/`: storage-agnostic domain and reusable business capabilities.
- `adapters/`: vendor, persistence, graph, vector, and storage implementations.
- `infra/`: portable systemd, Windows, and Supabase assets.
- `schemas/`: versioned interchange contracts.
- `docs/`: architecture, ADRs, contracts, and operations.

CI rejects root-level `src/`, `frontend/`, `windows/`, `supabase/`, and systemd units so the previous repository layout cannot silently return.

## Dependency rule

```text
apps -> packages -> protocols <- adapters
```

Forbidden directions and authority violations:

- packages importing application code;
- domain entities importing Supabase, Graphiti, Cognee, Qdrant, Next.js, model SDKs, systemd, or Windows APIs;
- publication code reading raw private evidence without an explicit authorized use case;
- generated artifacts or search indexes becoming the only copy of a claim or revision;
- public repository files becoming the canonical store for private journals, identities, or raw evidence.

## Domain foundation already implemented

The `memory-domain` package currently enforces:

1. accepted claims require at least one provenance reference;
2. evidence references identify a source object and episode, with optional utterance and time spans;
3. revisions are append-only status-change records;
4. timestamps are timezone-aware;
5. generated artifacts reference canonical episode or claim IDs;
6. publication uses a separate decision record;
7. ingestion idempotency is represented by `source_hash + pipeline_version`.

These models establish the contract. They do not yet prove that the current runtime persists all production data through the v2 schema.

## Migration phases

### Phase 0: freeze and inventory

Repository implementation:

- read-only SHA-256 inventory tooling;
- file counts, byte totals, hashes, duplicate detection, Git tracking state, and current commit recording;
- public/private repository boundary validation;
- prohibition on destructive migration without inventory evidence.

Still required in the operating environment:

- execute and retain the inventory against all production evidence and artifacts;
- export the current Supabase schema, migration history, row counts, key ranges, buckets, complete paginated object manifests, RLS, and Storage policies;
- retain recoverable backups before any relocation or deletion.

### Phase 1: establish public repository boundaries

Implemented in repository:

- introduce `apps/`, `packages/`, `adapters/`, `infra/`, and `schemas/`;
- relocate the Python runtime to `apps/capture-vrchat/src/`;
- relocate the Next.js reader to `apps/reader/`;
- consolidate systemd, Windows, and Supabase assets under `infra/`;
- remove fixed home-directory dependencies;
- make Cognee optional;
- update Taskfile, CI, tests, scripts, documentation, and agent workflows;
- reject reintroduction of the old root layout.

Still required in the operating environment:

- install and verify the rendered systemd units on the production host;
- verify Windows Task Scheduler and watchdog behavior on the actual machine;
- set the Vercel Root Directory to `apps/reader` and verify deployment;
- verify the relocated runtime against live Supabase and actual recording/GPU workloads.

### Phase 2: private memory repository

Not implemented:

- create private `KAFKA2306/kafka-memory`;
- add journal, memory, source-manifest, feedback, generated-view, and policy boundaries;
- keep binary evidence outside Git;
- make the private repository the reviewed human-memory surface used by assistants.

### Phase 3: canonical persistence

Foundation only; production persistence is not implemented:

- add PostgreSQL migrations for source objects, episodes, utterances, moments, entities, claims, revisions, artifacts, ingestion runs, outbox events, and publication decisions;
- assign stable UUIDs and migrate existing rows/files;
- enforce `source_hash + pipeline_version` idempotency;
- replace directory scans with explicit ingestion and outbox state;
- preserve append-only corrections and provenance.

### Phase 4: private storage migration

Not implemented:

- move raw audio, photos, video, transcripts, and documents to private object storage;
- retain complete manifests and hashes;
- separate private evidence buckets from public projection buckets;
- reconcile every source before deleting legacy copies.

### Phase 5: retrieval and MCP

Not implemented beyond reserved boundaries:

- PostgreSQL full-text search plus pgvector hybrid retrieval;
- read-first tools such as `search`, `timeline`, `get_evidence`, and `list_open_loops`;
- approval surfaces for write, correct, forget, and publish actions;
- optional Graphiti, Cognee, or Qdrant projections rebuilt from canonical stores.

### Phase 6: legacy removal

Not implemented:

- reconcile all files, rows, objects, hashes, and publication states;
- remove date/file-existence processing state and directory-wide synchronization;
- remove old schemas and compatibility paths;
- use Git history and retained inventories as rollback evidence rather than preserving permanent compatibility shims.

## Acceptance state

Completed in repository:

- public repository boundaries exist;
- old root runtime paths are rejected by CI;
- provenance-free accepted claims are rejected by the domain model;
- portable repository paths and systemd templates exist;
- read-only inventory tooling exists;
- current tests and builds pass on the relocated tree.

Not yet accepted:

- public OSS contains no production private data, confirmed by a complete production inventory;
- every accepted production memory is traceable to migrated evidence;
- repeated ingestion cannot create duplicate production records;
- corrections persist as production revisions;
- storage enumeration remains complete beyond provider page limits;
- public/private policy is enforced by live database and Storage policy;
- the private memory repository exists and is used;
- narrative artifacts can be deleted and regenerated from canonical memory;
- legacy files and schemas can be removed without loss.

## Rollback

Repository structural work is isolated in Git history. Raw evidence must not be modified as part of a code-only rollback. Data migrations require their own exported manifests, backups, reconciliation results, and reverse procedure.
