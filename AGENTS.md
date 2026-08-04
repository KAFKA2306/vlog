# AGENTS.md

Public OSS engine for capturing evidence, deriving reviewable human-memory claims, generating narrative artifacts, and publishing only explicitly approved projections.

## Mandatory audit rule

Before searching for `.agy`, verify whether the Antigravity CLI is installed and integrated:

1. `which agy`
2. `agy --version`
3. `agy --help`
4. `agy /usage`
5. search Taskfile, systemd units, tmux launchers, shell scripts, and cron jobs for `agy`

The canonical runtime identifier is `agy`, not `.agy`. Absence of `.agy` does not prove that Antigravity is absent.

## Repository boundaries

- `apps/`: deployable capture, reader, API, and MCP entry points.
- `packages/`: storage-agnostic domain, ingestion, narrative, privacy, and observability logic.
- `adapters/`: PostgreSQL, Supabase Storage, Graphiti, Cognee, and Qdrant implementations.
- `infra/`: Supabase migrations, systemd units, and Windows automation.
- `schemas/`: versioned interchange contracts.
- `docs/`: architecture, ADRs, and operating procedures.

The current `src/` and `frontend/reader/` paths are legacy runtime locations during migration. New Human Memory v2 capabilities belong in the target boundaries. Do not create new personal diary or memory content in this public repository.

## Canonical pointers

- [Human Memory v2 architecture](docs/architecture/human-memory-v2.md)
- [Phase 0 inventory runbook](docs/operations/phase0-inventory.md)
- [Current architecture](docs/architecture.md)
- [Daily pipeline contract](docs/daily_pipeline_contract.md)
- [Architecture decisions](docs/adr/)
- [Python coding rules](.claude/rules/python_coding.md)
- [General rules](.claude/rules/general.md)
- [Commands](.claude/rules/commands.md)
- [Model protection](.claude/rules/model_protection.md)
- [Task runner](Taskfile.yaml)

All repository pointers must be relative Markdown links. Do not add user-specific `file://` or absolute home-directory paths.

## Data and privacy rules

- Raw audio, photo, video, full transcript, and personal conversation evidence are private-object-storage data, not Git content.
- Private journals, people, relationships, preferences, corrections, and feedback belong in the private `kafka-memory` repository.
- AI output starts as a candidate. It is not an accepted memory or publication decision.
- Accepted memory claims must retain provenance to an episode/source and, where available, an utterance or time span.
- Graphiti, Cognee, pgvector, and Qdrant are rebuildable projections, never the sole source of truth.
- Structural migrations must not delete or move raw evidence until Phase 0 inventory and remote exports are complete.

## Verification

Run the relevant checks before completing work:

```bash
task lint
task test
uv run --no-sync python scripts/check_repository_boundaries.py
uv run --no-sync python scripts/phase0_inventory.py
```

Do not report runtime, Supabase, Windows, or systemd validation as complete unless it was executed in the corresponding operating environment.
