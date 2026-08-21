# Cross-platform portability contract

Status: accepted repository architecture; actual-host verification remains separate.

Tracking: #99. Decision record: [ADR-0012](../adr/0012-cross-platform-portability.md).

## Core decision

**physical path is not authority**.

| Concern | Authority |
|---|---|
| code/release identity | Git commit SHA |
| Evidence identity | stable source ID + content hash |
| remote Evidence location | object URI/key |
| environment identity | explicit environment/project/config |
| local absolute path | runtime locator only |

A machine-local path may locate bytes for one process. It must not become the durable identity of code, Evidence, memory, or a release.

## Checkout topology

```text
GitHub commit SHA
    ├── Windows-native checkout -> VRChat / physical audio / Task Scheduler
    ├── WSL/Linux-native checkout -> processing / systemd / Linux GPU work
    └── disposable CI checkout
```

Windows and WSL/Linux must not require the same physical code checkout. Windows-mounted WSL paths, WSL UNC shares, and general UNC paths are boundary locations, not canonical production code checkouts.

Evidence transport is a separate concern. Until #73 completes private object-storage cutover, an explicit legacy data bridge may exist without making the code checkout shared.

## Path support matrix

| Path class | Windows production code | WSL/Linux production code | Boundary use |
|---|---|---|---|
| local Windows drive path | supported | foreign | supported through explicit adapter |
| native POSIX path | foreign | supported | supported through explicit adapter |
| WSL Windows-mounted drive path | n/a | not canonical | migration/interoperability only |
| WSL UNC share | not canonical | n/a | migration/interoperability only |
| other UNC | not canonical | foreign | best-effort adapter only |
| spaces / Japanese / Unicode | supported | supported | CI-covered |
| case-only collisions | rejected in Git tree | rejected in Git tree | rejected |
| trailing dot/space or Windows reserved names | rejected in Git tree | rejected in Git tree | rejected |

Long-path support is not used as a design requirement. Keep checkout/generated path depth reasonable rather than assuming every Windows tool is long-path-aware.

## Project-root resolution

Runtime root precedence is:

1. explicit `VLOG_PROJECT_ROOT` when supplied and valid;
2. deterministic script/module location and repository-marker discovery;
3. invocation cwd only as diagnostic context, never authority.

PowerShell uses `$PSScriptRoot`; batch launchers use `%~dp0`; Python uses module/script location plus `pyproject.toml` discovery.

## Configuration and mutable state

Environment variable names use the canonical uppercase `VLOG_*` namespace. Secrets belong to platform secret/environment stores, not Git.

Portable target locations are:

- Linux config: XDG config home (`~/.config/vlog` default)
- Linux state: XDG state home (`~/.local/state/vlog` default)
- Linux cache: XDG cache home (`~/.cache/vlog` default)
- Windows config: roaming AppData `VLog`
- Windows state/cache: local AppData `VLog`

`apps/capture-vrchat/src/vlog_capture/portability.py` resolves these locations without creating them. Legacy repo-local `data/` remains an explicit migration state until #84/#73 cut it over non-destructively.

## Executables and toolchains

Supervised runtimes do not rely on an interactive shell profile. Executables are resolved and recorded before registration/rendering where practical.

- Windows Scheduled Task: absolute `cmd.exe`, explicit `WorkingDirectory`, resolved `uv.exe` handed to the launcher.
- systemd: rendered checkout root and `uv` executable.
- CI: runner-provided workspace and tool setup actions.

Python-minor-specific NVIDIA paths must not be constructed as strings. Discover installed NVIDIA package locations at runtime.

## Python package migration

The current capture application is still imported as `src`, and current CI/systemd/task assets still carry legacy `PYTHONPATH`. This remains **implemented legacy behavior**, not the target design. #82 removes it through installable packages/uv workspace. Documentation must not claim that migration is already complete.

## Verification boundary

Repository portability is continuously checked by:

- Windows-compatible Git filename checker;
- `.gitattributes` normalization;
- Ubuntu + Windows portability jobs;
- PowerShell parser checks;
- portability unit tests;
- read-only `scripts/vlog_doctor.py`.

These checks do **not** establish physical-host operation. VRChat process detection, physical audio, GPU transcription, Task Scheduler, systemd recovery, live Supabase, and full VRChat-to-KafLog flow remain environment-verified only through #67-#75.

## Primary references

See [2026 portability references](../references/portability-2026.md).
