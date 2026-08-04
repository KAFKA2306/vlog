# Windows and WSL error map

| Symptom | Boundary to inspect | Evidence |
|---|---|---|
| scheduled task does not start | Task Scheduler registration and action | task definition, last result, Windows event log |
| WSL command cannot find repository | path translation and configured project root | resolved command and working directory |
| systemd user manager unavailable | WSL/systemd configuration | `systemctl --user` result and journal |
| watchdog repeatedly restarts | heartbeat freshness and service failure | watchdog log, heartbeat JSON, service journal |
| command works interactively only | environment and credentials | sanitized environment differences |

Do not hard-code a particular machine, user, drive, or WSL distribution in the fix. See [Windows guide](../../../../infra/windows/README.md).
