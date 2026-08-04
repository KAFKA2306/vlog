---
name: windows-cmd-ps1-ops
description: Operate VLog Windows bootstrap, Task Scheduler, WSL bridge, and watchdog safely.
---

# Windows operations

Canonical Windows assets live under `infra/windows/`.

- Resolve the repository root from configuration or script location; do not embed a personal home path.
- Quote paths and distinguish Windows, WSL, and UNC semantics.
- Do not treat a successful WSL command as proof that Task Scheduler or the Windows watchdog works.
- Verify the registered task, action, working directory, logs, WSL distribution, service state, and an actual recording transition on the target machine.
- Redact secrets and private paths from shared logs.

See [Windows guide](../../../infra/windows/README.md).
