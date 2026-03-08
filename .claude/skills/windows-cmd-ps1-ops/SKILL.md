---
name: windows-cmd-ps1-ops
description: Windows operations protocol for running and recovering VLog via `run.bat`, `bootstrap.ps1`, and the Rust monitor. Trigger this skill when users hit UNC path launch failures, missing cargo/toolchain issues, ExecutionPolicy or permission blockers, restart-loop incidents, or Windows-side logging/debugging needs, because these failures are platform-specific and require exact command sequencing.
---

# Windows CMD/PS1 Ops

## 1. Responsibility Split
- `windows/run.bat` is the entry point for environment setup only.
- `src/windows/rust/bootstrap.ps1` is the control plane for build, toolchain discovery, and restart flow.
- `vlog-rs.exe monitor` is the execution target.

## 2. Path and Toolchain Normalization
- Normalize paths with `Resolve-Path` and avoid direct UNC execution.
- Use temporary drive mapping (`pushd`) when needed to enforce stable `C:\` execution context.
- If `where.exe cargo` fails, check `$env:USERPROFILE\.cargo\bin` explicitly.

## 3. Recovery Rules
- On abnormal process exit, restart after a short fixed delay.
- Prevent duplicate monitor instances by checking existing processes before launch.

## 4. Logging Rules
- Truncate startup bootstrap logs before each run.
- Keep log fields explicit: `timestamp`, `resolved_path`, `exit_code`, `working_dir`.

## 5. Definition of Done
- After `run.bat`, the monitor stays alive for at least 10 seconds.
- Windows process detection works and recording files appear in `data/recordings`.
- Crash reason is written to `logs/windows-rust-bootstrap.log`.
