---
name: systemd-maintenance
description: Manage VLog user services, portable unit templates, logs, and recovery. Activate for systemd, service, timer, startup, status, or journal issues.
allowed-tools:
  - "Bash(task *)"
  - Read
---

# Systemd Maintenance Skill

## Canonical Assets

- Templates: `infra/systemd/*.service.in`, `infra/systemd/*.timer.in`
- Renderer: `infra/systemd/render.py`
- Installer: `infra/systemd/install.sh`
- Installed units: `${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/`

Repository templates contain placeholders rather than a fixed checkout path. Never edit the rendered user units as the source of truth.

## Operations

```bash
task systemd:verify
task systemd:install
task service:status
task logs
task down
```

`task systemd:verify` renders into a temporary directory before `systemd-analyze verify`. `task systemd:install` renders the current repository and `uv` paths, reloads the user manager, enables the daily timer, and restarts the monitor.

## Failure Diagnosis

1. Run `systemctl --user status vlog.service vlog-daily.timer`.
2. Inspect `journalctl --user -u vlog.service -u vlog-daily.service`.
3. Compare the installed unit with the corresponding `.in` template.
4. Re-run `task systemd:verify` before installation.
5. Check `data/heartbeats/` and the operations report.

Do not claim Linux/WSL runtime success from static CI alone.
