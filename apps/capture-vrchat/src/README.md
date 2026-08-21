# VRChat capture source tree

`src/` is the Python source-layout directory. The import package is [`vlog_capture/`](vlog_capture/).

## Package boundaries

- `vlog_capture/domain/`: provider-independent entities and protocols.
- `vlog_capture/use_cases/`: capture, processing, generation, evaluation, and publication orchestration.
- `vlog_capture/infrastructure/`: audio, AI, storage, system, settings, and observability adapters.
- `vlog_capture/cli.py` and `vlog_capture/cli_handlers.py`: command-line wiring.
- `vlog_capture/daily.py`: scheduled orchestration.
- `vlog_capture/operations.py`: diagnosis and operational reporting.

Runtime values come from configuration, environment, and portability-aware settings. Do not duplicate volatile values in this README.

The current application still includes legacy-compatible file/artifact state while Human Memory v2 canonical ingestion is being built. See [current architecture](../../../docs/architecture.md) and [portability contract](../../../docs/architecture/portability.md).
