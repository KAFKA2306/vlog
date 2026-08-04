# VLog Reader

The Reader is a Next.js application under `apps/reader/`. It presents current diary and narrative projections while the v2 review and publication model is being built.

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
