# ADR-0005: external prompt asset integration

## Status

Accepted for prompt assets; audited 2026-08-04.

## Context

Prompt text can drift when copied across code, configuration, and agent instructions. An external prompt repository can provide reviewed prompt assets and change history.

## Decision

Prompt assets may be synchronized through an explicit repository task. The public VLog repository retains only the configuration and code required to consume those assets.

The external prompt source is not canonical human memory, evidence storage, or a substitute for versioned runtime configuration. Synchronization must not copy private journals, people data, secrets, or unreviewed personal memory into this public repository.

## Consequences

- Prompt changes can be reviewed independently from runtime code.
- Runtime execution remains reproducible only when the synchronized revision and configuration are recorded.
- Missing external access is an environment condition and must not be reported as a successful synchronization.

## References

- [Maintenance](../MAINTENANCE.md)
- [Human Memory v2](../architecture/human-memory-v2.md)
