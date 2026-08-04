---
name: photo-pipeline
description: Operate VLog image generation through direct photo tasks and automatic generation after novel build. Trigger this skill for image backfills, `task photo`/`task photos` failures, or consistency checks between direct and automatic generation.
allowed-tools:
  - Read
  - "Bash(task *)"
disable-model-invocation: true
argument-hint: "[novel-or-date]"
---

# Photo Pipeline Skill

## Scope
- Handle direct image generation with `task photo novel=...`.
- Handle bulk generation with `task photos`.
- Handle automatic image generation triggered from `task novel:build`.

## Canonical Paths
- Task entry: `Taskfile.yaml` (`photo`, `photos`, `novel:build`)
- Generator implementation: `apps/capture-vrchat/src/infrastructure/ai.py`
- Automatic orchestration: `apps/capture-vrchat/src/use_cases/build_novel.py`
- Output: `data/photos/`

## Required Checks
1. Confirm the novel input exists.
2. Confirm the output resolves under `data/photos/`.
3. Confirm direct and automatic paths instantiate the same image generator implementation.
4. Compare arguments and configuration before changing model/runtime code.

## Output Contract
- State the entry point used.
- State the implementation that generated the image.
- State the output path.
- Isolate task wiring, use-case wiring, dependencies, or model/runtime as the failure domain.
