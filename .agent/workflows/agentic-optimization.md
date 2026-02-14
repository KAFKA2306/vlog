---
description: Procedures for agentic health check and maintenance of the vlog project.
---

# Agentic Management Workflow

Follow these steps to ensure the project remains in a healthy state and all data is processed correctly.

## 1. Health Survey
- Run `task status` to verify `systemd` unit states.
- Check `journalctl --user -n 50 -u vlog` for any persistent errors in the audio pipeline.
- Verify `supabase` connectivity by running `task sync`.

## 2. Processing Audit
// turbo
- Run `task process:pending` to catch any files missed by the auto-pipeline.
- Check `data/recordings` vs `data/summaries` to ensure 1:1 mapping for processed dates.
- Run `task photos:fill` to identify and generate missing photos for past entries.

## 3. Maintenance
- Run `task lint` to ensure code stability.
- Run `task clean` if local caches (e.g., Whisper, Python) are consuming excessive disk space.
- Perform a Git commit using `task commit MESSAGE="Maintenance: [Summary of changes]"` if any automatic fixes were applied.
