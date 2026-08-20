---
name: windows-cmd-ps1-ops
description: Operate VLog Windows bootstrap, Task Scheduler, capture, and watchdog under the 2026 portability contract.
---

# Windows operations

Canonical Windows assets live under `infra/windows/`.

- Use a Windows-native checkout for Windows production responsibilities. Do not make UNC, `\\wsl$`, or `\\wsl.localhost` the canonical code checkout.
- Resolve repository root from explicit configuration or script location (`$PSScriptRoot` / `%~dp0`), never from a personal home path or invocation cwd.
- Scheduled Task actions must have an explicit `WorkingDirectory` and resolved executable paths; do not rely on an interactive PowerShell profile or user-only PATH mutation.
- Path conversion is a boundary operation, not the architecture. Coordinate Windows and WSL checkouts by Git commit SHA.
- A successful parser/CI/WSL command is not proof that Task Scheduler, VRChat detection, physical audio, or watchdog recovery works. Verify those on the target host.
- Redact secrets and private paths before sharing diagnostics; prefer `python scripts/vlog_doctor.py --redact`.

See [portability architecture](../../../docs/architecture/portability.md) and [Windows guide](../../../infra/windows/README.md).
