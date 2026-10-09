# 2026-02-20 cross-platform path incident

Status: historical incident record; not current service status

## Scope

A Windows/WSL invocation used an environment-specific repository path and failed before the intended VLog command could run. The original record also linked to a machine-local task file that was never tracked in Git.

## Root cause

The command path and working directory were treated as fixed machine facts rather than resolved runtime configuration. This mixed Windows, WSL, and repository-relative path semantics.

## Corrective direction

The accepted successor decision is [ADR-0012](../adr/0012-cross-platform-portability.md): **physical path is not authority**.

- Windows and WSL/Linux use separate native production code checkouts.
- Git commit SHA identifies the code version across checkouts.
- Local paths are runtime locators, not Evidence/release identity.
- systemd and Task Scheduler use explicit working directories and resolved executables.
- cross-filesystem path conversion is limited to explicit boundary/migration adapters.
- repository CI checks portable filenames before Windows checkout/runtime use.
- actual Task Scheduler/WSL/audio/GPU behavior is still verified on the target host.

## Current relevance

The original machine paths are obsolete. This record is retained as rationale only; current normative behavior is defined by [`../architecture/portability.md`](../architecture/portability.md).
