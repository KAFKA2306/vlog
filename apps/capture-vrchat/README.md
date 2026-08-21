# VRChat capture application

This application contains the current Python capture and processing runtime.

The installable package is `vlog_capture`. Package metadata and console entry points are defined in [`pyproject.toml`](pyproject.toml); repository tasks are defined in [`../../Taskfile.yaml`](../../Taskfile.yaml). Runtime `PYTHONPATH` and the former `src` package name are not part of the current execution contract.

Responsibilities:

- VRChat process observation and audio capture;
- transcription orchestration;
- current legacy-compatible artifact generation;
- synchronization to current projections;
- operational evidence and diagnosis.

Canonical Human Memory v2 persistence is a separate target architecture. See [current runtime architecture](../../docs/architecture.md) and [Human Memory v2 architecture](../../docs/architecture/human-memory-v2.md).
