# systemd

Portable user-unit templates and the installation path for the Linux/WSL runtime.

The repository stores `*.service.in` and `*.timer.in` templates. `render.py` resolves the current checkout, the absolute `uv` executable, and the VLog config/data/state/cache homes, then writes concrete units outside the repository. No user home or checkout location is committed into a unit.

The Git checkout is read-only at runtime. Mutable files are written only below the OS-standard VLog homes (or explicit `VLOG_CONFIG_HOME`, `VLOG_DATA_HOME`, `VLOG_STATE_HOME`, `VLOG_CACHE_HOME` overrides). Secrets are not loaded from a repository `.env`. If a dotenv file is required, set `VLOG_ENV_FILE` to an explicit absolute path before rendering/installing the units.

Install and start:

```bash
task systemd:install
```

Before installation, the installer resolves `uv` and `systemctl` to absolute executable paths and prints their versions. It then reuses those exact paths for the entire registration run, so an interactive shell alias/function or later PATH lookup cannot change the executable mid-run. Diagnose resolution without changing service state:

```bash
infra/systemd/install.sh --diagnose
```

`VLOG_UV_EXE` and `VLOG_SYSTEMCTL_EXE` may be set to explicit absolute executable paths. Missing, relative, or non-executable paths fail before unit rendering or service registration.

After upgrading or moving `uv`/`systemctl`, rerun `task systemd:install`. This re-resolves the executables, re-renders the units with the current absolute `uv` path, reloads the user manager, and restarts/enables the service/timer. Do not edit the rendered units by hand.

Validate rendered units without installing:

```bash
task systemd:verify
```

The installer writes units to `${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user`, creates the runtime homes, reloads the user manager, enables the daily timer, and restarts the monitor service. Entry points are installed from the uv workspace (`vlog`, `vlog-service`, `vlog-operations`); the daily timer runs `vlog daily`. Unit files do not construct Python import paths.

## VRCPet / Muchio observation ingest

The daily pipeline includes the `vrcpet:ingest` stage. Configure the source and, when
needed, a private evidence root in the external `VLOG_ENV_FILE`:

```dotenv
VLOG_VRCPET_ROOT=/mnt/<drive>/<VRCPet-data-root>
VLOG_PRIVATE_EVIDENCE_ROOT=/path/outside/the/checkout
```

The source root is read-only. If it is unset or unavailable, the stage records a
structured skip and the rest of the daily pipeline continues. Stable files are
content-addressed and recorded in the private state ledger, so rerunning the daily
timer does not duplicate observations. Raw observation bytes and conversation text
must remain outside the public checkout.

The same operation can be checked manually with `task vrcpet:ingest`. The normal
`vlog daily` timer invokes it automatically.
