# capture-vrchat

Python runtime for VRChat detection, recording, transcription, memory extraction, narrative generation, synchronization, and operational recovery.

The import package remains `src` during this behavior-preserving relocation, but its physical root is now `apps/capture-vrchat/src`. Runtime launchers set `PYTHONPATH=apps/capture-vrchat` explicitly. A future package-rename can occur independently from the repository-boundary migration.

```bash
PYTHONPATH=apps/capture-vrchat uv run python -m src.main
PYTHONPATH=apps/capture-vrchat uv run python -m src.cli --help
```

Business rules that become canonical Human Memory v2 capabilities move into `packages/`; vendor-specific implementations move into `adapters/`.
