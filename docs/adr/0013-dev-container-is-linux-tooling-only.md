# ADR-0013: Dev Container is Linux tooling only

Status: accepted 2026-08-20. Tracks #89.

## Decision

VLog provides a Dev Container to reproduce the **Linux/CI development toolchain**, not to emulate the Windows production host.

The container pins the repository-supported Python line, uv, Bun, and Task and runs `uv sync --locked` plus the Reader frozen install after creation. It intentionally contains no credentials, `.env` values, Supabase secrets, Vercel credentials, audio-device assumptions, or VRChat integration.

## In scope

- Python workspace installation and import checks;
- Ruff, pytest, type checking and repository contract checks;
- Reader install, tests, lint, typecheck and production build;
- systemd template rendering/verification where supported by the container host;
- optional future Linux GPU-worker development when GPU passthrough is explicitly configured.

## Out of scope

- VRChat process detection;
- physical Windows audio capture;
- Windows Task Scheduler registration/execution;
- proof that NVIDIA/CUDA works on the user's physical host;
- proof that a WSL user systemd manager is healthy;
- live Supabase/Vercel credentials or production state.

A green container therefore counts as repository/Linux-tooling verification only. It cannot close actual-host E2E issues #67-#75.

## Toolchain authority

The container reads no separate mise/asdf toolchain manifest. Version authority remains in existing repository contracts: `.python-version` and `requires-python` for Python, the Reader `packageManager` field for Bun, the CI/Dev Container uv pin, and the Task version documented by the portability/toolchain contract.
