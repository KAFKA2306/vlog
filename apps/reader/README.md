# VLog Reader

The Reader is a Next.js application under `apps/reader/`. It presents current diary and narrative projections while the v2 review and publication model is being built.

## Design system

`DESIGN.md` is the canonical visual contract for the public KafLog Reader. It defines the Quiet Memory / Editorial Archive direction, semantic color tokens, typography, content-type semantics, interaction rules, accessibility targets, and representative visual-regression views.

Implementation changes should consume semantic tokens rather than introducing component-local brand colors or restoring the previous black/cyan neon treatment.

## Development

Use repository tasks so dependency installation, type checking, linting, and production build remain aligned:

```bash
task web:dev
task web:build
task web:start
```

## Boundaries

- Browser code must not receive service-role credentials or unrestricted private-object URLs.
- Generated narratives and images must not be presented as canonical evidence.
- Private, review, and public states should be visually and semantically distinct.
- Deployment providers must use `apps/reader/` as the application root.

A successful build does not prove the live Vercel configuration or Supabase policy behavior.
