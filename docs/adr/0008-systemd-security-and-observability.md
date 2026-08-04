# ADR-0008: portable systemd supervision

## Status

Accepted; audited 2026-08-04.

## Context

Committed systemd units containing a fixed checkout or user path are not portable. Service supervision also needs structured failure evidence without leaking private data into notifications.

## Decision

Version-controlled units are templates under `infra/systemd/`. The renderer resolves the current repository root and writes concrete user units outside Git. The monitor and daily services use explicit failure handlers and local operational evidence.

Repository verification checks rendered syntax. Installation, user-manager availability, timer timezone behavior, watchdog operation, and actual service execution require verification on the target host.

## Consequences

- A checkout can move without editing committed unit paths.
- The renderer and templates become part of the deployment contract.
- CI success does not establish that the user's systemd manager is available or configured.

## References

- [systemd README](../../infra/systemd/README.md)
- [Operations](../OPERATIONS.md)
