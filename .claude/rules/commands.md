# Commands & Workflows

## Core Tasks

- `task setup`: Sync dependencies (`uv sync`).
- `task dev`: Run monitor in dev mode.
- `task lint`: Format and lint with `ruff`.
- `task status`: Check systemd & log status.

## Operation Tasks

- `task process FILE=...`: Process a specific recording.
- `task process:all`: Batch process all recordings.
- `task novel:build`: Generate daily novel.
- `task sync`: Sync with Supabase.

## Git Protocol

- `task commit MESSAGE="..."`: Stage and commit changes.
- Use `/git` workflow for repository maintenance.
