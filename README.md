# VLog Human Memory Engine

Public OSS engine for capturing VRChat evidence, deriving reviewable human-memory claims, generating narrative artifacts, and publishing only explicitly approved projections.

> Migration status: Human Memory Repository v2 Phase 0/1. The current runtime remains operational in legacy `src/` and `frontend/reader/` locations while canonical boundaries, inventory, and schemas are introduced. See [Issue #14](https://github.com/KAFKA2306/vlog/issues/14).

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

Diaries and novels are generated views, not canonical memory. AI-extracted claims begin as `candidate`; accepted claims require provenance to source evidence.

## Repository boundaries

```text
vlog/
├── apps/                  deployable capture, reader, API, and MCP entry points
├── packages/              domain, ingestion, narrative, privacy, observability
├── adapters/              PostgreSQL, Storage, Graphiti, Cognee, Qdrant
├── infra/                 Supabase migrations, systemd, Windows automation
├── schemas/               versioned evidence and memory contracts
├── docs/                  architecture, ADRs, and operations
├── src/                   legacy runtime during migration
└── frontend/reader/       legacy Next.js reader during migration
```

Private personal data is deliberately outside this public repository:

```text
KAFKA2306/vlog             public OSS engine
KAFKA2306/kafka-memory     private journal and reviewed memory views
private object storage     raw audio, photo, video, and full evidence
public site                explicitly approved projections only
```

## Current capabilities

- VRChat process monitoring and automatic audio capture
- Faster Whisper transcription
- Gemini-based diary and narrative generation
- illustration generation
- Supabase synchronization and Next.js reader
- systemd and Windows supervision
- structured operational audit and recovery tooling

## Setup

Requirements: Python 3.11+, [uv](https://github.com/astral-sh/uv), and [Task](https://taskfile.dev).

```bash
git clone https://github.com/KAFKA2306/vlog.git
cd vlog
uv sync
cp .env.example .env
```

Common commands:

```bash
task dev
task test
task lint
task up
task status
task sync
task web:dev
```

## Phase 0 inventory

Before relocating or deleting any legacy evidence, create a read-only SHA-256 inventory:

```bash
uv run --no-sync python scripts/phase0_inventory.py
uv run --no-sync python scripts/check_repository_boundaries.py
```

The inventory records file counts, bytes, hashes, Git tracking state, duplicate content, and the current commit. It does not delete, move, upload, or rewrite evidence.

## Canonical rules

- PostgreSQL/Supabase, private object storage, and the private memory repository are canonical stores.
- Graphiti, Cognee, pgvector, and Qdrant are rebuildable projections.
- raw evidence is private by default;
- publication is a separate explicit decision;
- ingestion idempotency uses `source_hash + pipeline_version`;
- corrections append revisions rather than destroying prior values;
- directory scans and file existence are legacy processing mechanisms, not the v2 state model.

## Documentation

- [Human Memory v2 architecture](docs/architecture/human-memory-v2.md)
- [Phase 0 inventory runbook](docs/operations/phase0-inventory.md)
- [Current architecture](docs/architecture.md)
- [Daily pipeline contract](docs/daily_pipeline_contract.md)
- [Operations](docs/OPERATIONS.md)
- [Agent router](AGENTS.md)

Production reader: [kaflog.vercel.app](https://kaflog.vercel.app)
