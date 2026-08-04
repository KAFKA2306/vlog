---
name: model-guard
description: Protect VLog model configuration from unrequested changes.
---

# Model guard

Apply this skill when changing `data/config.yaml`, model-related settings, AI adapters, or embedding configuration.

1. Read the current config and consuming code.
2. Do not infer a newer or preferred model name.
3. Change a model identifier only when the user explicitly requests that change.
4. Keep runtime selections and fallback behavior consistent.
5. Run focused configuration tests and the repository quality gate.

The current repository, not this skill file, is authoritative for actual model names.
