---
name: wsl-path-bridge
description: Handle Windows/WSL path boundaries without making path translation or a shared checkout the architecture.
---

# WSL path bridge

Primary rule: **do not solve portability by continually translating the canonical repository path.**

- Keep Windows production code in a Windows-native checkout and WSL/Linux production code in a Linux-native checkout.
- Use Git commit SHA to prove both checkouts run the same version.
- Classify foreign paths lexically before filesystem access; use `PureWindowsPath` / `PurePosixPath` semantics, not host-dependent guessing.
- `/mnt/<drive>`, `\\wsl$`, `\\wsl.localhost`, and UNC paths are explicit boundary locations, not canonical production code checkouts.
- Translate/copy a path only inside an adapter or migration boundary. Do not persist the translated machine-local path as Evidence identity.
- Until private object-storage transport is complete, legacy data bridging may remain explicit and temporary; do not turn it back into a shared code checkout.
- Fail with an actionable message when a foreign/unsupported path crosses a runtime boundary.

Use `python scripts/vlog_doctor.py` for read-only diagnosis. See [portability architecture](../../../docs/architecture/portability.md).
