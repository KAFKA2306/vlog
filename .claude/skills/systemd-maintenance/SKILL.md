---
name: systemd-maintenance
description: Maintain VLog portable systemd templates and verify live installation separately.
---

# systemd maintenance

Templates live under `infra/systemd/` and are rendered for the current checkout.

```bash
task systemd:verify
task systemd:install
```

- Change templates, renderer, tests, and documentation together.
- `task systemd:verify` proves rendered syntax only.
- After installation, inspect unit files, timer schedule, timezone behavior, service status, and journal in the actual user manager.
- Do not hard-code a user home or checkout path in version control.

See [systemd README](../../../infra/systemd/README.md) and [operations](../../../docs/OPERATIONS.md).
