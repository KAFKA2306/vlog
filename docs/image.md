---
codd:
  node_id: "req:image-generation"
  type: spec
  status: approved
  links:
    - to: apps/capture-vrchat/src/infrastructure/ai.py
      type: implementation
---

# Illustration generation boundary

Status: current legacy-compatible runtime; generated output is a rebuildable narrative artifact

## Responsibility

The current pipeline can derive an illustration prompt from narrative text, run a configured Diffusers pipeline, save the prompt record, and write an image artifact. The implementation is in `apps/capture-vrchat/src/infrastructure/ai.py`; configuration loading is in `apps/capture-vrchat/src/infrastructure/settings.py` and `data/config.yaml`.

This document does not duplicate current model names or dependency versions. Read the configuration and manifests before making an operational claim.

## Flow

```text
narrative text
    -> optional embedded IMAGE_PROMPT or configured prompt-generation model
    -> configured prompt filters and negative prompt
    -> configured image pipeline
    -> prompt record and image artifact
```

The generator chooses a random seed when no seed is supplied and records that seed in structured trace metadata. Actual GPU availability, memory use, runtime, and visual quality require execution in the target environment.

## Data classification

- Source recordings and photos are private evidence.
- Generated prompts and illustrations are derived artifacts.
- Generated images must retain a reference to their source episode, claim, or current legacy input during migration.
- Generation does not authorize publication.
- Public projection requires a separate publication decision and privacy review.

## Configuration discipline

Before changing image behavior:

1. inspect `data/config.yaml`;
2. inspect settings defaults and the consuming adapter;
3. preserve prompt and seed traceability;
4. avoid silent model or output-format changes;
5. test CPU/GPU fallback and failure reporting where relevant.

## Operations

Use tasks defined in `Taskfile.yaml` for generation and Reader validation. Verify:

- prompt file and image output are non-empty;
- trace metadata identifies model, output path, and seed when available;
- failed generation exits visibly and does not create a false success artifact;
- private inputs are not copied into public Reader assets;
- publication state is independent from generation state.

## Migration target

Human Memory v2 will persist artifact identity, provenance, generation metadata, privacy level, and publication decisions in canonical storage. File existence and date-based names remain current legacy mechanisms until migration and reconciliation are complete.

See [Human Memory v2 architecture](architecture/human-memory-v2.md) and [current runtime architecture](architecture.md).
