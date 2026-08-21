# ADR-0012: Physical path is not authority

Status: accepted  
Date: 2026-08-20  
Tracking: #99

## Context

VLog spans Windows-native VRChat/audio capture, WSL/Linux processing and systemd, GitHub Actions, Vercel, Supabase, and private Evidence storage. Historical failures came from treating a checkout path, cwd, shell PATH, or OS-specific filesystem behavior as a stable machine fact.

A shared Windows/WSL code checkout reduces clone count but couples the runtime to cross-filesystem semantics, path translation, permissions, lifecycle, and performance. Persisting local absolute paths also makes data identity change when the repository moves.

## Decision

VLog adopts the rule **physical path is not authority**.

1. Code/release identity is Git commit SHA.
2. Evidence identity is stable source ID plus content hash.
3. Remote Evidence location is object URI/key.
4. Environment identity is explicit project/environment/configuration.
5. Local path is a runtime locator only.
6. Windows and WSL/Linux production code use separate native checkouts.
7. Path translation is confined to boundary adapters/migration compatibility.
8. Supervised processes use explicit working directories and resolved executables.
9. Repository filenames must be representable on Windows and POSIX.
10. CI portability evidence is not substituted for actual-host E2E evidence.

## Consequences

Positive:

- repository relocation and drive changes stop changing durable identity;
- Windows and Linux filesystem semantics are isolated;
- Task Scheduler/systemd behavior becomes diagnosable;
- CI can enforce filename/path contracts before host deployment;
- future private object storage can replace legacy data bridging without changing identity.

Costs:

- Windows and WSL require separate clones;
- a transitional Evidence/data bridge remains until object-storage cutover;
- current `src`/`PYTHONPATH` and repo-local `data/` require staged migration rather than destructive replacement.

## Rejected alternatives

- Treat `/mnt/c` or `\\wsl$` shared checkout as the canonical topology.
- Solve every failure with automatic `wslpath`/drive-letter conversion.
- Add another toolchain authority such as mise/asdf solely to mask existing uv/Task configuration drift.
- Claim container/CI PASS proves Windows VRChat/audio or systemd host operation.

## Verification

Repository verification is defined in [`../architecture/portability.md`](../architecture/portability.md). Actual-host guarantees remain tracked by #67-#75.
