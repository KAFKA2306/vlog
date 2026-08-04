# ADR-0010: external Reader integration

## Status

Accepted; audited 2026-08-04.

## Context

Generated narrative projections need a separate user-facing surface. The Reader must not collapse private evidence, review state, and public publication into one implicit state.

## Decision

The Reader is a deployable Next.js application under `apps/reader/`. It consumes authorized projection data and must not receive service-role credentials or unrestricted private-object access.

Local typecheck, lint, and build are repository evidence. Deployment-provider root configuration, deployed revision, environment variables, and live Supabase policy behavior require separate environment verification.

## Consequences

- Reader development and deployment are isolated from the capture runtime.
- Public projection remains an explicit decision rather than a side effect of generation.
- Deployment configuration becomes part of the cutover checklist.

## References

- [Reader README](../../apps/reader/README.md)
- [Human Memory v2](../architecture/human-memory-v2.md)
