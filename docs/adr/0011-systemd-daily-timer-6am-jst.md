# ADR-0011: daily timer at 09:00 local time

## Status

Accepted; audited 2026-08-04.

## Context

The current daily pipeline needs a predictable execution window that avoids the primary interactive VRChat session. The schedule was changed to 09:00.

## Decision

`infra/systemd/vlog-daily.timer.in` schedules the current daily service at 09:00 with persistence enabled. The template currently relies on the host's local timezone rather than embedding a timezone identifier.

The installed timer must therefore be inspected on the target host. Repository syntax verification does not prove the intended Asia/Tokyo trigger time or that a catch-up execution occurred.

## Consequences

- The intended production schedule is documented in one timer template and the daily pipeline contract.
- Host timezone drift can change the actual trigger time.
- Schedule changes require template, contract, tests, and live timer verification.

## References

- [Current daily pipeline contract](../daily_pipeline_contract.md)
- [Operations](../OPERATIONS.md)
