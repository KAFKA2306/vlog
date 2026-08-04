---
name: frontend-design
description: Design and implement the VLog Reader with accessible, evidence-aware UI.
---

# Reader design

The Reader lives in `apps/reader/`. Design for private/public state clarity rather than decorative novelty.

- Make evidence status, generated status, and publication status distinguishable.
- Preserve semantic structure, keyboard navigation, visible focus, contrast, responsive behavior, and reduced motion.
- Do not imply that an AI-generated narrative is canonical memory.
- Do not expose private object URLs, service-role credentials, or raw evidence in public views.
- Reuse existing visual language unless the task explicitly calls for a redesign.
- Run `task web:build` and perform browser-level accessibility review for UI changes.

See [Reader README](../../../apps/reader/README.md).
