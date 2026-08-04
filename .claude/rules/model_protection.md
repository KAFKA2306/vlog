---
paths:
  - "data/config.yaml"
  - "apps/capture-vrchat/src/infrastructure/settings.py"
  - "apps/capture-vrchat/src/infrastructure/ai.py"
  - "apps/capture-vrchat/src/infrastructure/cognee.py"
---

# Model configuration protection

Before changing a model identifier, read `data/config.yaml`, `apps/capture-vrchat/src/infrastructure/settings.py`, and the consuming implementation.

- Do not change model identifiers without explicit user instruction.
- Treat `data/config.yaml` as the current runtime selection where a key exists.
- Treat implementation fallbacks as compatibility behavior, not permission to silently upgrade or downgrade.
- Keep transcription, generative, image, and embedding model settings distinct.
- Validate configuration loading and the affected runtime path after an authorized change.
