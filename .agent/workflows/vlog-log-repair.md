---
description: Procedures for diagnosing and repairing log errors in the vlog project.
---

# VLog Log Repair Workflow

Follow these steps to autonomously diagnose and repair data pipeline failures. Fixes MUST be evidence-based.

## 1. Evidence Gathering (Context7)
// turbo-all
1. **Trace Logs**: Extract specific failure points from `vlog.log`.
   ```bash
   tail -n 100 data/logs/vlog.log | grep -E "Error|Exception"
   ```
2. **Fact Check**: Verify physical file paths for any reported `FileNotFoundError`.
   ```bash
   ls -l data/recordings/
   ```

## 2. Autonomous Repair Loop
// turbo-all
1. **Run Repair Agent**: Force a reconciliation of `tasks.json`.
   ```bash
   task repair
   ```
2. **Verify Path Normalization**: Ensure no `\` remains in `tasks.json`.
   ```bash
   grep "\\\\" data/tasks.json
   ```

## 3. Recovery Processing
// turbo-all
1. **Process Catch-up**:
   ```bash
   task process:all
   ```
2. **Backfill Integrity**: Ensure novels and summaries exist for all recordings.
   ```bash
   task process:pending
   ```

## 4. Final Sync & Verification
// turbo-all
1. **Supabase Sync**: Push repaired states to cloud.
   ```bash
   task sync
   ```
2. **Termination Evidence**: Successful completion of repair MUST be marked in `vlog.log`.

## 5. Escalation
- If repair fails, create `docs/logs/YYYYMMDD_crash_analysis.md` following [mcp-context.md](file:///home/kafka/projects/.claude/rules/mcp-context.md) rules.
