---
name: io-manager
description: Audit VLog evidence and artifact file lifecycle without destructive assumptions.
---

# IO manager

- Run the Phase 0 inventory before destructive migration or cleanup.
- Never delete raw evidence because a summary, database row, or upload appears to exist.
- Require a retained manifest, hashes, backup or private-storage object, and reconciliation evidence.
- Distinguish raw evidence, current legacy artifacts, canonical metadata, and rebuildable projections.
- Use paginated remote listings until exhaustion.
- Keep cleanup changes explicit and reviewable; do not use broad deletion patterns.

See [Phase 0 runbook](../../../docs/operations/phase0-inventory.md) and [maintenance](../../../docs/MAINTENANCE.md).
