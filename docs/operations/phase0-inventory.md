# Phase 0 Inventory Runbook

This procedure freezes the source evidence layout before relocation. It does not delete, move, upload, or rewrite source files.

## Local inventory

```bash
uv run --no-sync python scripts/phase0_inventory.py
```

Optional explicit roots:

```bash
uv run --no-sync python scripts/phase0_inventory.py \
  --evidence-root data/recordings \
  --evidence-root data/transcripts \
  --evidence-root data/photos
```

The command writes `data/inventory/phase0-<UTC timestamp>.json`. The `data/` ignore policy prevents this machine-local inventory from being committed accidentally.

Each record contains:

- repository-relative path;
- category;
- byte size and UTC modification timestamp;
- SHA-256 digest;
- Git tracking state;
- symlink state and target.

The summary includes category totals, tracked evidence count, and duplicate hash groups.

Use the stricter mode after private source files have been removed from Git:

```bash
uv run --no-sync python scripts/phase0_inventory.py --fail-on-tracked-evidence
```

## Repository boundary check

```bash
uv run --no-sync python scripts/check_repository_boundaries.py
```

This check rejects:

- personal memory repository roots committed to public `vlog`;
- tracked raw audio/video;
- tracked files above 100 MiB;
- escaping symlinks;
- user-specific absolute pointers in `AGENTS.md`;
- missing v2 top-level boundaries.

## Supabase inventory

The local command cannot prove remote completeness. Before Storage or schema migration, export and retain the following from the operating environment:

1. database schema and migration history;
2. row counts and primary-key ranges for every table;
3. Storage bucket list, visibility, object count, total bytes, and paginated object manifest;
4. RLS and Storage policies;
5. public/private state of every generated artifact;
6. a hash or immutable export reference for each export file.

Do not use a single `list(..., limit=1000)` response as a complete inventory. Continue pagination until the provider reports no remaining page.

## Exit criteria

Phase 0 is complete only when:

- local inventory JSON exists and is retained outside the public repository;
- remote exports are complete and independently restorable;
- raw evidence deletion is disabled operationally;
- counts and byte totals are recorded in the migration PR or private operations log.
