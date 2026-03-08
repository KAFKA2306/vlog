---
name: ollama-gpt-oss-fallback
description: Fallback protocol for temporary Gemini failures using local Ollama `gpt-oss:20b`. Trigger this skill when Gemini calls fail with transient errors (for example 429/503, timeout, or temporary unavailability), because local fallback keeps processing unblocked without waiting for external API recovery.
allowed-tools:
  - "Bash(wsl.exe *)"
  - Read
  - Edit
disable-model-invocation: true
argument-hint: "[task-or-file]"
---

# Ollama GPT-OSS Fallback Skill

## Scope
- Use local `ollama` with `gpt-oss:20b` when Gemini is temporarily unavailable.
- Keep workflow minimal: detect transient Gemini failure, switch to local model, run the target task, then report outcome.

## Trigger Conditions
- Gemini returns transient API errors (429, 500, 502, 503, timeout).
- Logs indicate temporary model unavailability or rate limiting.
- User asks to continue processing immediately without waiting for Gemini recovery.

## Preconditions
- `ollama` command is available.
- `ollama serve` is running.
- `gpt-oss:20b` exists in `ollama list`.

## Canonical Checks
1. `wsl.exe -d Ubuntu-22.04 --cd /home/kafka/projects/vlogrs sh -lc 'command -v ollama && ollama list'`
2. `wsl.exe -d Ubuntu-22.04 --cd /home/kafka/projects/vlogrs sh -lc 'ps aux | grep -E "ollama serve" | grep -v grep'`

## Execution Policy
- Treat this as a temporary fallback path only.
- Do not silently switch models; explicitly state fallback activation and reason.
- Keep command path stable via WSL:
  - `wsl.exe -d Ubuntu-22.04 --cd /home/kafka/projects/vlogrs sh -lc '<command>'`

## Suggested Task Flow
1. Confirm Gemini failure is transient from logs/error output.
2. Confirm local model readiness (`ollama serve`, `gpt-oss:20b` present).
3. Execute the requested processing task through the local fallback path.
4. Report:
   - Original Gemini error
   - Fallback model used (`gpt-oss:20b`)
   - Task result and output location

## Output Contract
- Always include explicit fallback reason.
- Always include exact command used.
- Always distinguish transport/model failure from task logic failure.
