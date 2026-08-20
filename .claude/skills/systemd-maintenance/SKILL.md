---
name: systemd-maintenance
description: Maintain VLog portable systemd templates and verify live installation separately.
---

# systemd maintenance

Templates live under `infra/systemd/` and are rendered for the current Linux/WSL-native checkout.

```bash
task systemd:verify
task systemd:install
```

- Keep the production WSL/Linux checkout on its native Linux filesystem; `/mnt/<drive>` is not the canonical code checkout.
- Resolve checkout root from renderer/script location or explicit configuration, not invocation cwd.
- Render explicit `WorkingDirectory` and resolved `ExecStart` executables. Do not rely on an interactive shell PATH.
- Keep environment authority explicit. Shell `source`, systemd `EnvironmentFile`, and Pydantic dotenv parsing must not silently disagree.
- `PYTHONPATH` in rendered units is legacy compatibility only and must disappear with the uv-workspace migration (#82).
- Change templates, renderer, tests, and documentation together.
- `task systemd:verify` proves rendered syntax only. Actual service/timer/journal/failure recovery requires host verification (#71).

See [portability architecture](../../../docs/architecture/portability.md), [systemd README](../../../infra/systemd/README.md), and [operations](../../../docs/OPERATIONS.md).
