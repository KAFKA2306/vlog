---
name: wsl-path-bridge
description: Resolve Windows PowerShell <-> WSL Ubuntu command bridge failures and path translation errors. Trigger this skill when commands fail with shim launch errors, `wsl bash -lc` failures, `Failed to translate '\\\\wsl.localhost\\...'`, missing shell errors, or mixed Windows/WSL cwd issues, because execution usually succeeds only after switching to a stable `wsl.exe -d <distro> --cd <linux-path> sh -lc '<cmd>'` form.
allowed-tools:
  - "Bash(wsl.exe *)"
  - Read
disable-model-invocation: true
---

# WSL Path Bridge Skill

## Scope
- Fix command execution failures caused by PowerShell shim launch issues and Windows-to-WSL path translation breaks.
- Establish one reliable command form for reproducible execution.

## Trigger Patterns
- PowerShell shim errors launching tools.
- `wsl bash -lc ...` fails.
- `wsl: Failed to translate '\\wsl.localhost\...'`.
- `/bin/sh: bash: not found`.
- Command works only after explicit distro + `--cd`.

## Canonical Execution Form
- Always switch to:
  - `wsl.exe -d Ubuntu-22.04 --cd /home/kafka/projects/vlogrs sh -lc '<command>'`
- Do not use UNC cwd as execution root.
- Do not depend on `bash -lc` if `bash` is unavailable; use `sh -lc`.

## Minimal Recovery Workflow
1. Verify task runner path from WSL:
   - `wsl.exe -d Ubuntu-22.04 --cd /home/kafka/projects/vlogrs sh -lc 'task --version'`
2. Verify environment file presence:
   - `wsl.exe -d Ubuntu-22.04 --cd /home/kafka/projects/vlogrs sh -lc 'if [ -f .env ]; then echo ENV_FILE_PRESENT; else echo ENV_FILE_MISSING; fi'`
3. Verify required keys are set:
   - `wsl.exe -d Ubuntu-22.04 --cd /home/kafka/projects/vlogrs sh -lc 'grep -E "^(GOOGLE_API_KEY|SUPABASE_URL|SUPABASE_SERVICE_ROLE_KEY|GEMINI_MODEL)=" .env | sed "s/=.*$/=***set***/"'`
4. Run target task:
   - `wsl.exe -d Ubuntu-22.04 --cd /home/kafka/projects/vlogrs sh -lc 'task process FILE=data/recordings/20260224_192304.wav'`

## Failure Mapping
- If shim fails: bypass shim and run command through `wsl.exe`.
- If `wsl bash -lc` fails: switch to `wsl.exe -d ... --cd ... sh -lc`.
- If task fails with YAML parse: fix `Taskfile.yaml` syntax first, then rerun.
- If app exits non-zero after command path is valid: inspect app logs and return the exact root cause.

## Output Contract
- Report exact command used.
- Report pass/fail with concrete stderr/stdout reason.
- Separate transport/path failures from app/runtime failures.
