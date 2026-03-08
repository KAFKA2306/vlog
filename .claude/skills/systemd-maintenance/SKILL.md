---
name: systemd-maintenance
description: Manage and maintain systemd units for the VLog project, including `vlog.service`, `vlog-daily.service`, and `vlog-daily.timer`. ACTIVATE this skill whenever the user mentions "systemd", "service", "logs", "status", or if the core monitor fails to start automatically. It handles `task up`, `task down`, `task restart`, and `task logs`. Use this proactively to ensure the long-term stability of the background processes.
allowed-tools:
  - "Bash(task *)"
  - Read
---

# Systemd Maintenance Skill

A specialized skill for managing the lifecycle and health of VLog's background services using systemd.

## Core Operations

### 1. Service Control
Enable, start, or stop the background monitor and daily task timers.
- **cmd**: `task up` (Enables and starts all units)
- **cmd**: `task down` (Stops and disables all units)
- **cmd**: `task restart` (Restarts the main `vlog` service)

### 2. Status and Health Checks
Monitor the current state of services.
- **cmd**: `task service:status` (Checks the main monitor status)
- **cmd**: `task status` (Runs the app-level status command)

### 3. Log Analysis
Investigate failures or crashes.
- **cmd**: `task logs` (Tails the journal for the `vlog` unit)
- When a crash is detected (e.g., monitor exit), immediately check logs to identify the root cause.

## Unit Files
The systemd units are located in:
- `systemd/vlog.service`: Main recording monitor.
- `systemd/vlog-daily.service`: Daily processing task.
- `systemd/vlog-daily.timer`: Timer for the daily task.

## Guidelines
- **User Mode**: All `systemctl` commands MUST use the `--user` flag (handled by Taskfile).
- **Proactive Maintenance**: If the user reports the app isn't working, first check `task service:status`.
- **Silent Troubleshooting**: Analyze logs before asking the user for input on crashes.

## Examples
- "Start it in the background" -> `task up`
- "Check whether the service is running" -> `task service:status`
- "Show logs after an error" -> `task logs`
- "Stop daily scheduled execution" -> `task down` (or individual systemctl commands)
