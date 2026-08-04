# Packages

Reusable business capabilities live here and remain independent from deployment frameworks.

- `memory-domain/`: canonical entities and invariants.
- `ingestion/`: hashing, inventory, idempotency, provenance, and outbox contracts.
- `narrative/`: diary, novel, illustration, and review generation.
- `privacy/`: redaction, pseudonymization, retention, and publication gates.
- `observability/`: operational events, traces, health, and audit reporting.

Dependency direction is `apps -> packages -> adapter protocols`. Search indexes and vendor SDKs are not canonical domain dependencies.
