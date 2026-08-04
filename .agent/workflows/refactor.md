---
description: Human Memory v2 boundariesを維持しながら安全にリファクタリングする手順
---

# Refactor workflow

## Invariants

- Do not delete or relocate raw evidence during a code-only refactor.
- Keep runtime, reader, infrastructure, package, adapter, and schema boundaries distinct.
- Packages must not import application code.
- Accepted memory claims require provenance.
- Search and graph systems remain rebuildable projections.
- Do not simplify by deleting tests, typing, error context, observability, comments, or safe exception handling.

## Procedure

1. Inspect the current implementation and executable entry points.
2. Decide whether the change requires a Phase 0 inventory or remote export.
3. Update code, Taskfile, CI, deployment assets, and documentation as one coherent change.
4. Run:

```bash
task lint
task test
task doc:check
task systemd:verify
task web:build
```

5. Perform OS, deployment, database, storage, or GPU checks in the actual environment when those boundaries changed.
6. Follow the [Git workflow](git.md).

A refactor is complete only for the boundaries that were actually validated.
