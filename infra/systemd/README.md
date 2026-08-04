# systemd

Portable user-unit templates and the installation path for the Linux/WSL runtime.

The repository stores `*.service.in` and `*.timer.in` templates containing `@VLOG_ROOT@`, `@VLOG_PYTHONPATH@`, and `@VLOG_UV@`. `render.py` resolves the current checkout path and writes concrete units outside the repository. No user home or checkout location is committed into a unit.

Install and start:

```bash
task systemd:install
```

Validate rendered units without installing:

```bash
task systemd:verify
```

The installer writes units to `${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user`, reloads the user manager, enables the daily timer, and restarts the monitor service.
