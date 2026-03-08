---
name: photo-pipeline
description: Operate VLog image generation through both entry points: direct photo tasks and automatic generation after novel build. Trigger this skill when users ask to generate images from novels, backfill missing images, debug `task photo` or `task photos`, or verify that `novel:build` and the Rust image wrapper use the same underlying pipeline, because image generation must stay consistent across both execution paths.
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

## Trigger Conditions
- User asks to generate an image from a novel file.
- User asks to fill missing images for existing novels.
- `task photo` fails.
- Rust novel generation succeeds but image generation fails.
- User wants to confirm both code paths use the same generator.

## Canonical Paths
- Task entry: `Taskfile.yaml` `photo` and `photos`
- Python generator: `src/scripts/image_gen.py`
- Rust wrapper: `src/infrastructure.rs` `PythonImageGenerator`
- Automatic path: `src/use_cases/build_novel.rs`

## Required Checks
1. Confirm the novel input exists.
2. Confirm the output path resolves under `data/photos/`.
3. Confirm both task and Rust wrapper call the same Python generator script.
4. If one path fails and the other works, compare arguments first before changing code.

## Output Contract
- State which entry point was used.
- State which script generated the image.
- State output file path.
- If broken, isolate whether the failure is task wiring, Rust wrapper wiring, Python dependencies, or model/runtime failure.
