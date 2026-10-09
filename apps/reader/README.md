# VLog Reader

The Reader is a Next.js application under `apps/reader/`. It presents current diary and narrative projections while the v2 review and publication model is being built.

## Design system

`DESIGN.md` is the canonical visual contract for the public KafLog Reader. It defines the Quiet Memory / Editorial Archive direction, semantic color tokens, typography, content-type semantics, interaction rules, accessibility targets, and representative visual-regression views.

Implementation changes should consume semantic tokens rather than introducing component-local brand colors or restoring the previous black/cyan neon treatment.

## Public projection inputs

The Reader consumes public projections only.

- Diary uses the current public Diary/local-development archive boundary and keeps `/day/[date]` as its detail route.
- Novel reads public rows from the historical `novels` projection using the public Supabase anon boundary. `is_public=eq.true` is part of the request, explicitly private rows are rejected defensively, and `/novels/[id]` uses the canonical Novel row ID as the stable permalink. `image_url` is optional; older public rows without that field remain readable.
- `People Said / 人から言われたこと` reads `data/public/social_mirror.jsonl` when that projection exists.

Diary and Novel are both narrative artifacts, but they are not presented as the same kind of record. Diary is a human-readable record of a day rather than raw Evidence; Novel is explicitly labeled as a creative derivative from memory rather than a factual record.

People Said rows follow `schemas/social-mirror-public-projection.schema.json`. Reader parsing rejects records that carry raw/private source fields such as `EvidenceRef`, source-object IDs, transcript text, source excerpts, or internal speaker entity IDs. Missing projection files produce an empty state rather than falling back to canonical/private data.

`context` and `reaction` are optional public-projection annotations. Their absence is displayed as absence; the Reader does not infer either value from a quote, Diary, or raw source.

## Development

Use repository tasks so dependency installation, type checking, linting, and production build remain aligned:

```bash
task web:dev
task web:build
task web:start
```

Reader contract tests run with Bun and are included in CI.

## Boundaries

- Browser code must not receive service-role credentials or unrestricted private-object URLs.
- Generated narratives and images must not be presented as canonical evidence.
- Private, review, and public states should be visually and semantically distinct.
- Deployment providers must use `apps/reader/` as the application root.

A successful build does not prove the live Vercel configuration or Supabase policy behavior.
