# ADR-0009: transcription model selection

## Status

Accepted; audited 2026-08-04.

## Context

Transcription model, device, and compute type affect latency, memory use, recognition quality, and competition with VRChat. Those values can change independently and must not be copied into multiple documents.

## Decision

The current runtime selection is read from `data/config.yaml` through the settings layer. Changes to the transcription model, device, or compute type require explicit review and focused runtime validation.

Historical speed, parameter-count, and memory figures are not treated as current evidence. Benchmarks must record hardware, input duration, model revision, compute type, and measured quality or error criteria.

## Consequences

- Configuration remains the current selection authority.
- GPU execution still requires live validation and resource protection.
- Model changes cannot be justified solely by a generic benchmark or newer name.

## References

- [Current runtime architecture](../architecture.md)
- [Resource-aware processing](0004-resource-protection-for-gpu-stability.md)
