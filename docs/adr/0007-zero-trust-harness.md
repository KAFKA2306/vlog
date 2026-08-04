# ADR-0007: evidence-based runtime harness

## Status

Accepted; audited 2026-08-04.

## Context

A process exit code or a single log line is insufficient to establish that capture, generation, synchronization, or recovery behaved correctly. Failures also need durable identity so recovery cannot close an unrelated incident.

## Decision

Operational verification correlates structured events, component and resource identity, trace context, heartbeat freshness, process state, source files, outputs, and downstream visibility. Recovery explicitly references the failure it resolves.

Secrets, raw evidence, and detailed private logs remain local and are not copied into public Reader content or brief notifications.

## Consequences

- False success and false recovery become testable failure modes.
- More operational evidence must be retained and rotated safely.
- Repository tests validate semantics, while live supervision and notification delivery require environment verification.

## References

- [Operations](../OPERATIONS.md)
- [Maintenance](../MAINTENANCE.md)
