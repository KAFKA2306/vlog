---
name: io-manager
description: Manage the data lifecycle and file I/O operations of the VLog project. ACTIVATE this skill whenever the user mentions "archiving", "storage", "disk space", "cleaning up files", or "moving data". It ensures that recordings in `data/recordings/` are correctly processed and moved to `data/archives/`, and that temporary `.wav.part` files are managed. Use this proactively to prevent storage bottlenecks and maintain high data integrity.
---

# IO Manager Skill

A skill designed for robust data lifecycle management, ensuring storage efficiency and data durability in the VLog ecosystem.

## Core Workflows

### 1. Ingestion Management
Monitor and clean up the ingestion pipeline.
- **Check + process pending**: `task process:pending`
- **Check status**: `task status`
- If direct file operations are required, propose a new `Taskfile` task first.

### 2. Archival Process
Move processed content from active areas to long-term storage.
- **Single file process**: `task process FILE=path/to/file.wav` (Archives automatically after success).
- **Batch process**: `task process:all` or `task process:today`.

### 3. Integrity Verification
Ensure that the filesystem structure matches the `src/infrastructure/settings.py` definitions.
- Verify the existence of required directories (archives, photos, novels, summary, etc.).
- Check for "orphaned" files (e.g., a summary with no source recording).

### 4. Storage Optimization
Identify large files or unneeded build artifacts.
- **Audit/Cleanup**: `task clean`
- **Action**: Suggest adding dedicated `task storage:audit` and `task archive:*` commands when lifecycle automation is needed.

## Guidelines
- **Integrity First**: NEVER delete a recording unless it has been confirmed as synchronized to Supabase or backed up.
- **Safety**: Any destructive operation requires explicit user instruction.
- **Zero-Fat**: Keep IO operations minimal and fast.
