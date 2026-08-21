---
name: io-manager
description: Audit VLog Evidence and artifact lifecycle without treating machine-local paths as identity.
---

# IO manager

- Run the Phase 0 inventory before destructive migration or cleanup.
- Never delete raw Evidence because a summary, database row, or upload appears to exist.
- Treat a local absolute path as a runtime locator only. Canonical Evidence identity is a stable source ID plus content hash; remote location is an object URI/key.
- Require retained manifests, byte sizes, hashes, backup/private-storage objects, remote readback, and reconciliation evidence before cleanup.
- The same bytes must keep the same Evidence identity across Windows, WSL, Linux, relocation, or drive changes.
- Separate code checkout from mutable config/state/cache. Use the portability runtime-directory contract while #84 migrates legacy repo-local state.
- Distinguish raw Evidence, legacy artifacts, canonical metadata, and rebuildable projections.
- Use paginated remote listings until exhaustion and keep cleanup explicit/reviewable.

See [portability architecture](../../../docs/architecture/portability.md), [Phase 0 runbook](../../../docs/operations/phase0-inventory.md), and [maintenance](../../../docs/MAINTENANCE.md).
