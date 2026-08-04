# VRChat capture runtime

## Boundaries

- `domain/`: entities and protocols without provider dependencies.
- `use_cases/`: orchestration of capture, processing, generation, evaluation, and publication checks.
- `infrastructure/`: audio, AI, storage, system, settings, and observability adapters.
- `cli.py` and `cli_handlers.py`: command-line wiring.
- `daily.py`: current scheduled orchestration.
- `operations.py`: diagnosis and operational reporting.

Runtime values come from `data/config.yaml`, environment variables, and settings defaults. Do not duplicate them in this README.

The current application still uses date/file-based state and local artifact directories. Those are legacy-compatible mechanisms scheduled for replacement by canonical IDs, ingestion runs, and outbox state. See [current architecture](../../../docs/architecture.md).
