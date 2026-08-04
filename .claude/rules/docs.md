---
paths:
  - "**/*.md"
  - "**/*.markdown"
---

# Documentation rules

- Start at [docs/README.md](../../docs/README.md) and update the existing authority instead of creating a parallel specification.
- Use repository-relative links and paths.
- Link to `Taskfile.yaml`, `pyproject.toml`, package manifests, schemas, and code instead of copying volatile inventories.
- Distinguish implemented in repository, CI-verified, environment-verified, historical, and planned states.
- Point-in-time incidents belong under `docs/incidents/`; they must not be presented as current service status.
- Run `task doc:check`.
