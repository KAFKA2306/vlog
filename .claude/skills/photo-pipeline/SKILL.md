---
name: photo-pipeline
description: Operate and review VLog illustration generation as a rebuildable narrative projection.
---

# Illustration pipeline

The current implementation is documented in [docs/image.md](../../../docs/image.md).

- Read `data/config.yaml`, settings, and the image adapter before citing model or output parameters.
- Treat generated images and prompts as derived artifacts, not evidence.
- Preserve source references, seed metadata when available, and generation failure context.
- Do not publish generated media without a separate publication decision.
- Verify GPU execution and output quality in the actual runtime environment.
