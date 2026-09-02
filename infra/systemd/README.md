# systemd

Portable user-unit templates and the installation path for the Linux/WSL runtime.

The repository stores `*.service.in` and `*.timer.in` templates. `render.py` resolves the current checkout, the absolute `uv` executable, and the VLog config/data/state/cache homes, then writes concrete units outside the repository. No user home or checkout location is committed into a unit.

The Git checkout is read-only at runtime. Mutable files are written only below the OS-standard VLog homes (or explicit `VLOG_CONFIG_HOME`, `VLOG_DATA_HOME`, `VLOG_STATE_HOME`, `VLOG_CACHE_HOME` overrides). Secrets are not loaded from a repository `.env`. If a dotenv file is required, set `VLOG_ENV_FILE` to an explicit absolute path before rendering/installing the units.

Install and start:

```bash
task systemd:install
```

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
