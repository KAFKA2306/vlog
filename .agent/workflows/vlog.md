---
description: VLogの診断、実行、復旧、データ完全性確認を行う手順
---

# VLog operations workflow

Use [docs/OPERATIONS.md](../../docs/OPERATIONS.md) as the normative runbook and [docs/daily_pipeline_contract.md](../../docs/daily_pipeline_contract.md) for the current scheduled flow.

## Diagnose

```bash
task status
uv run python -m src.operations doctor --root "$(pwd)"
uv run python -m src.operations report --days 30
```

Correlate process state, journal entries, structured events, heartbeat freshness, source files, and generated outputs. WSL success is not Windows verification.

## Operate

```bash
task dev
task process:daily
task sync
task systemd:verify
task web:build
```

Commands that install units, modify Task Scheduler, deploy the Reader, or contact Supabase require the relevant environment and credentials.

## Recover

1. Preserve raw inputs and logs.
2. Identify the failed component and resource.
3. Fix the cause at its canonical boundary.
4. Run focused checks, then the full relevant gate.
5. Replay only the affected idempotent operation.
6. Verify output, audit evidence, and downstream visibility.
7. Record any environment validation that remains unexecuted.
