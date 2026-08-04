---
codd:
  node_id: "req:overview"
  type: spec
  status: approved
  links:
    - to: apps/capture-vrchat/src/main.py
      type: implementation
    - to: docs/architecture/human-memory-v2.md
      type: architecture
---

# VLog overview

VLog captures evidence from VRChat sessions and turns it into reviewable memory and narrative artifacts. The long-term system is a Human Memory Engine, not a diary generator whose AI summary becomes the source of truth.

## Product direction

```text
Evidence -> Human Memory -> Narrative Artifact -> Public Projection
```

- **Evidence**: raw audio, photos, video, full transcripts, source hashes, and provenance spans.
- **Human Memory**: episodes, moments, entities, claims, revisions, decisions, preferences, and open loops.
- **Narrative Artifact**: diaries, novels, illustrations, and periodic reviews generated from canonical memory.
- **Public Projection**: artifacts released only through a separate publication decision.

AI-generated text is a derived view. It must not silently replace evidence or reviewed memory.

## Two architectures coexist during migration

### Current executable runtime

The current application remains file-based so the repository relocation does not change production behavior. It:

1. detects VRChat and records audio;
2. transcribes recordings;
3. generates summaries, narrative artifacts, and images;
4. determines pending work from date-based filenames and missing artifacts;
5. synchronizes selected outputs to the current Supabase schema;
6. exposes them through the Next.js reader;
7. records operational events and supports systemd and Windows supervision.

This behavior is documented in [`architecture.md`](architecture.md) and [`daily_pipeline_contract.md`](daily_pipeline_contract.md). It is legacy-compatible, not the v2 canonical state model.

### Human Memory Repository v2 target

The target system uses stable IDs, content hashes, explicit ingestion runs, append-only revisions, an outbox, private object storage, and a separate private memory repository. It is documented in [`architecture/human-memory-v2.md`](architecture/human-memory-v2.md).

## Implementation status

As of 2026-08-04:

| Scope | Repository state | Environment state |
|---|---|---|
| Phase 0 inventory code and repository boundary checks | implemented | production inventory and Supabase/storage export pending |
| Phase 1 public repository boundaries and runtime relocation | implemented | Linux/WSL, Windows, Vercel, and live Supabase cutover pending |
| Phase 2 private `kafka-memory` repository | not implemented | not started |
| Phase 3 canonical memory persistence | domain foundation only | PostgreSQL migrations, outbox, and migration pending |
| Phase 4 private storage migration | not implemented | not started |
| Phase 5 retrieval and MCP | reserved boundaries only | not started |
| Phase 6 legacy removal | not implemented | blocked on reconciliation |

Repository implementation was established by [PR #15](https://github.com/KAFKA2306/vlog/pull/15) and the runtime relocation by [PR #16](https://github.com/KAFKA2306/vlog/pull/16). [Issue #14](https://github.com/KAFKA2306/vlog/issues/14) remains open for the unfinished migration.

## Repository responsibilities

- `apps/capture-vrchat/`: current capture and processing runtime.
- `apps/reader/`: current reader and future review/publication surface.
- `packages/`: reusable, storage-agnostic domain capabilities.
- `adapters/`: persistence, storage, graph, and vector implementations.
- `infra/`: systemd, Windows, and Supabase deployment assets.
- `schemas/`: versioned interchange contracts.
- `docs/`: architecture, ADRs, contracts, and operations.

The public repository must not become the canonical store for personal journals, identities, raw media, or private evidence.

## Core invariants

- An accepted memory claim requires provenance.
- Evidence and publication are separate concerns.
- Corrections append a revision; they do not erase history.
- Raw evidence is private by default.
- Graph and vector systems are rebuildable projections.
- Environment-specific work is not complete until executed and evidenced in that environment.
- No destructive migration occurs before a complete inventory and recoverable backup.

## Documentation routes

- [Documentation index](README.md)
- [Target architecture and migration phases](architecture/human-memory-v2.md)
- [Current runtime architecture](architecture.md)
- [Phase 0 inventory](operations/phase0-inventory.md)
- [Operations](OPERATIONS.md)
- [Maintenance](MAINTENANCE.md)
