# VLog Human Memory Engine

VLog is a public OSS engine for capturing VRChat evidence, producing reviewable memory claims and narrative artifacts, and publishing only explicitly approved projections.

Human Memory Repository v2 is an active migration tracked in [Issue #14](https://github.com/KAFKA2306/vlog/issues/14). The repository boundaries and behavior-preserving runtime relocation are implemented. Canonical persistence, private memory, private object-storage migration, and retrieval remain incomplete.

## Architecture

```text
Evidence
raw audio, photos, conversations, full transcripts
        ↓
Human Memory
episodes, moments, entities, claims, revisions
        ↓
Narrative Artifacts
diaries, novels, illustrations, monthly reviews
        ↓
Public Projection
explicitly approved artifacts only
```

Diaries, novels, illustrations, summaries, graph indexes, and vector indexes are derived views. They are not canonical memory. An accepted `MemoryClaim` requires provenance to source evidence.

## Current status

| Area | Status |
|---|---|
| `apps/`, `packages/`, `adapters/`, `infra/`, `schemas/` boundaries | implemented in repository |
| Canonical domain models and provenance invariant | implemented in repository |
| Read-only SHA-256 Phase 0 inventory tooling | implemented in repository; production inventory not yet executed |
| Runtime relocation to `apps/capture-vrchat/` and `apps/reader/` | implemented in repository |
| Portable systemd, Windows, and Supabase paths | implemented in repository; host cutover not yet verified |
| Private `kafka-memory` repository | planned |
| Canonical PostgreSQL schema, UUIDs, idempotency, and outbox | planned |
| Private object-storage migration and complete manifests | planned |
| Hybrid retrieval and read-first MCP | planned |
| Legacy file-state removal | planned after migration reconciliation |

GitHub CI validates repository behavior. It does not prove live systemd installation, Windows Task Scheduler behavior, Vercel configuration, Supabase contents or policies, private storage, or GPU execution.

## Repository boundaries

```text
vlog/
├── apps/
│   ├── capture-vrchat/   current Python capture and processing runtime
│   ├── reader/           current Next.js reader
│   ├── api/              reserved HTTP application boundary
│   └── mcp/              reserved read-first MCP boundary
├── packages/             storage-agnostic domain capabilities
├── adapters/             persistence, graph, vector, and storage integrations
├── infra/
│   ├── supabase/         current schema and migrations
│   ├── systemd/          portable unit templates and installer
│   └── windows/          Task Scheduler, bootstrap, and watchdog assets
├── schemas/              versioned interchange contracts
├── docs/                 architecture, ADRs, and operations
├── tests/                repository-level verification
└── data/                 machine-local evidence and generated artifacts
```

Private personal data is deliberately outside this public repository:

```text
KAFKA2306/vlog             public OSS engine
KAFKA2306/kafka-memory     private reviewed memory and journal views
private object storage     raw audio, photos, video, and full evidence
public site                explicitly approved projections only
```

## Current runtime

The relocated runtime preserves existing behavior while the v2 persistence model is built:

- VRChat process monitoring and audio capture;
- transcription and generated diary/narrative artifacts;
- file-based processing state and directory scans;
- Supabase synchronization and the Next.js reader;
- systemd and Windows supervision assets;
- operational audit and recovery tooling.

The Python import package intentionally remains named `src`. `Taskfile.yaml`, CI, systemd templates, and Windows scripts set the runtime path to `apps/capture-vrchat`.

## Setup

Requirements: Python 3.11+, [`uv`](https://github.com/astral-sh/uv), and [Task](https://taskfile.dev). Reader commands additionally require Bun.

```bash
git clone https://github.com/KAFKA2306/vlog.git
cd vlog
uv sync --frozen
cp .env.example .env
```

Common commands:

```bash
task dev
task test
task doc:check
task systemd:verify
task web:build
```

Operational commands such as `task up`, `task status`, `task sync`, and `task web:deploy` require their corresponding host credentials and services.

## Before data migration

Create a non-destructive inventory before relocating or deleting any legacy evidence:

```bash
uv run --no-sync python scripts/phase0_inventory.py
uv run --no-sync python scripts/check_repository_boundaries.py
```

The inventory records file counts, bytes, hashes, Git tracking state, duplicate content, and the current commit. It does not delete, move, upload, or rewrite evidence.

## Canonical rules

- Private object storage is canonical for raw evidence bytes.
- PostgreSQL/Supabase is the target canonical store for source metadata, memory entities, revisions, ingestion state, outbox events, and publication decisions.
- The private memory repository is canonical for reviewed journal text, policy, corrections, and human-maintained memory views.
- Graphiti, Cognee, pgvector, and Qdrant are rebuildable projections.
- Publication is a separate explicit decision.
- Target ingestion idempotency uses `source_hash + pipeline_version`.
- Corrections append revisions rather than destroying prior values.
- Directory scans and file existence are current legacy mechanisms, not the v2 state model.

## Documentation

Start with the [documentation index](docs/README.md).

- [Product overview and status](docs/overview.md)
- [Human Memory v2 target architecture](docs/architecture/human-memory-v2.md)
- [Current runtime architecture](docs/architecture.md)
- [Phase 0 inventory runbook](docs/operations/phase0-inventory.md)
- [Operations](docs/OPERATIONS.md)
- [Maintenance](docs/MAINTENANCE.md)
- [Current daily pipeline contract](docs/daily_pipeline_contract.md)
- [Agent router](AGENTS.md)

Production reader: [kaflog.vercel.app](https://kaflog.vercel.app)

## Documentation governance

All Markdown is governed by [docs/markdown-governance.md](docs/markdown-governance.md). Generic agent tutorials and point-in-time service status do not belong in the active documentation corpus.
