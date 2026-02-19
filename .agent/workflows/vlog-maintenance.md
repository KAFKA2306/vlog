---
description: Procedures for agentic health check and maintenance of the vlog project.
---

# VLog Health Maintenance Workflow

Follow these steps to ensure system health and total operational stability.

## 1. System Health Check
// turbo-all
1. **Service Status**:
   ```bash
   task status
   ```
2. **Crash Analysis**: If `vlog.log` contains errors, immediately transition to [vlog-log-repair.md](file:///home/kafka/projects/vlog/.agent/workflows/vlog-log-repair.md).
   ```bash
   tail -n 100 data/logs/vlog.log | grep -E "Error|Critical"
   ```

## 2. Zero-Fat Infrastructure Audit
// turbo-all
1. **Dependency Sync**: Ensure Supabase and local tasks are 1:1.
   ```bash
   task sync
   ```
2. **Process Audit**: Identify and process abandoned recordings.
   ```bash
   task process:pending
   ```

## 3. Code Integrity
// turbo-all
1. **Lint & Format**: Enforce strict coding standards.
   ```bash
   task lint
   ```
2. **Quality Verification**: Run health check suite.
   ```bash
   task check
   ```

## 4. Finalization
- **Evidence Collection**: Check `vlog.log` one last time for silence.
- **Commit State**:
  ```bash
  task commit MESSAGE="Maintenance: [Repair Summary]"
  ```
