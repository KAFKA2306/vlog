---
name: io-manager
description: Manage the data lifecycle and file I/O operations of the VLog project. ACTIVATE this skill whenever the user mentions "archiving", "storage", "disk space", "cleaning up files", or "moving data". It ensures that recordings in `data/recordings/` are correctly processed and moved to `data/archives/`, and that temporary `.wav.part` files are managed. Use this proactively to prevent storage bottlenecks and maintain high data integrity.
allowed-tools:
  - "Bash(task *)"
  - Read
  - Glob
disable-model-invocation: true
argument-hint: "[operation]"
---

# IO Manager Skill

A skill designed for robust data lifecycle management, ensuring storage efficiency and data durability in the VLog ecosystem.

## Core Workflows

### 1. Ingestion Management
Monitor and clean up the ingestion pipeline.
- **Check + process pending**: `task process:all`
- **Corrupted cleanup**: `task clean:corrupted`
- If direct file operations are required, propose a new `Taskfile` task first and avoid ad-hoc shell commands.

### 2. Archival Process
Move processed content from active areas to long-term storage.
- Prefer a dedicated `task` command for archival.
- Ensure that for every file in `data/archives/`, a corresponding summary exists to verify completion.

### 3. Integrity Verification
Ensure that the filesystem structure matches the `constants.rs` definitions.
- Verify the existence of required directories (archives, photos, novels, etc.).
- Check for "orphaned" files (e.g., a summary with no source recording).

### 4. Storage Optimization
Identify large files or unneeded build artifacts.
- **Audit/Cleanup**: `task clean` and `task clean:corrupted`
- **Action**: Suggest adding dedicated `task storage:audit` and `task archive:*` commands when lifecycle automation is needed.

## Guidelines
- **Integrity First**: NEVER delete a recording unless it has been confirmed as synchronized to Supabase or backed up.
- **Safety**: Any destructive operation requires explicit user instruction.
- **Zero-Fat**: Keep IO operations minimal and fast.

## Examples
- "I need to save disk space" -> Propose archival moves and temporary file cleanup.
- "Can you verify recordings are safely stored?" -> Check consistency between `data/recordings` and `data/archives`.
- "Organize data older than one month" -> Generate date-based move workflow.
- "Can I delete interrupted recording files?" -> Check `.wav.part` last-modified state and propose action.
