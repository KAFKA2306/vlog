# 2026-02-20 cross-platform path incident

Status: historical incident record; not current service status

## Scope

A Windows/WSL invocation used an environment-specific repository path and failed before the intended VLog command could run. The original record also linked to a machine-local task file that was never tracked in Git.

## Root cause

The command path and working directory were treated as fixed machine facts rather than resolved runtime configuration. This mixed Windows, WSL, and repository-relative path semantics.

## Corrective direction

- Resolve the repository root at runtime.
- Keep systemd units as rendered templates under `infra/systemd/`.
- Keep Windows and WSL launch logic under `infra/windows/`.
- Do not commit personal home paths or links to machine-local data.
- Verify Windows Task Scheduler and WSL behavior on the actual host.

## Current relevance

The repository relocation and portable path work supersede the original path examples. This incident remains as rationale for portability checks; it is not evidence that the current host is configured or healthy.
