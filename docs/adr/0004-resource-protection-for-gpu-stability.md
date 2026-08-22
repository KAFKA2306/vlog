# ADR-0004: resource-aware heavy processing

## Status

Accepted; audited 2026-08-04.

## Context

Transcription and image generation can contend with VRChat for GPU, CPU, memory, audio, and storage resources. Starting heavy work during an active session can degrade capture quality or destabilize the host.

## Decision

The current daily entry point checks VRChat state before heavy processing and exits without starting the heavy path when the application is active. Runtime resource checks and the current implementation remain authoritative.

The schedule itself is not part of this ADR. It is defined by `infra/systemd/vlog-daily.timer.in`; runtime supervision and verification are documented in `docs/OPERATIONS.md`.

## Consequences

- Interactive capture takes priority over derived-artifact generation.
- Work may be delayed and must remain safely replayable.
- A skipped run is not a successful processing run; operational evidence must distinguish the two.
- Live stability still requires verification on the actual host and GPU workload.

## References

- [Operations](../OPERATIONS.md)
- [Current runtime architecture](../architecture.md)
