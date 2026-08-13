# KafLog Reader Design System

Status: canonical for `apps/reader/`

## 1. Product character

KafLog is a **Quiet Memory / Editorial Archive**: a place to revisit selected fragments of a life over time.

The interface should feel closer to reading a personal archive than operating an AI dashboard.

### Principles

1. **Content first** — dates, photographs, diary text, stories, and remembered words are the visual hierarchy.
2. **Quiet hierarchy** — use spacing, typography, and subtle tone changes before shadows, animation, or decoration.
3. **Warm paper, not cyber glass** — the canonical appearance is a light editorial surface with warm neutrals.
4. **Meaning before color** — Diary, Novel, People Said, and Timeline must remain distinguishable without color perception.
5. **Long-form comfort** — typography and measure are optimized for Japanese prose and repeated reading.
6. **Evidence-aware presentation** — visual polish must never make generated narrative look like canonical evidence.

### Explicitly non-canonical

The previous black/cyan visual language is not the KafLog design system. Do not reintroduce the following as the default identity:

- black `#05070a` canvas
- cyan `#75e6ff` as the dominant accent
- radial neon glow
- glassmorphism as a primary surface treatment
- hover lift such as `translateY(...)`
- dramatic shadows or particle/3D decoration

## 2. Semantic color tokens

Components must consume semantic tokens. Do not scatter raw hexadecimal values through component styles.

```css
:root {
  /* Foundations */
  --color-canvas: #f5f4ef;
  --color-paper: #ffffff;
  --color-paper-soft: #fcfbf8;

  /* Text */
  --color-ink: #1a1c20;
  --color-ink-muted: #5f6f82;
  --color-ink-subtle: #6b7280;

  /* Primary identity */
  --color-accent: #0f766e;
  --color-accent-soft: rgba(15, 118, 110, 0.07);

  /* Structure */
  --color-border: rgba(26, 28, 32, 0.12);
  --color-border-strong: rgba(15, 118, 110, 0.36);

  /* Content semantics */
  --color-diary: #0f766e;
  --color-novel: #8a5a2f;
  --color-people-said: #76537a;

  /* States */
  --color-focus: #0f766e;
  --color-danger: #9f2d2d;
}
```

### Contrast notes

The canonical text colors are chosen so that normal-size text can meet WCAG 2.2 Contrast (Minimum) when used on the intended paper/canvas surfaces.

- `--color-ink` is the default body text.
- `--color-ink-muted` is the minimum muted text color intended for normal-size text on the warm canvas.
- `--color-ink-subtle` may be used only where the actual foreground/background pair is mechanically verified; do not assume it is suitable everywhere.
- content-semantic colors may be used as text/markers only when the concrete foreground/background pair passes the required contrast.

Color must never be the sole differentiator for content type, selected state, publication state, quote type, or evidence level.

## 3. Content-type semantics

All content types belong to one archive. They are not separate product themes.

### Diary

- Label: `Diary / 日記`
- Default paper surface.
- Teal semantic marker.
- Date and prose are primary; metadata remains secondary.
- A Diary is a narrative artifact, not raw evidence.

### Novel

- Label: `Novel / 物語`
- Warm brown semantic marker.
- Must include a textual explanation that it is a creative/narrative derivative.
- Typography may feel slightly more literary, but must remain in the same KafLog system.

### People Said

- Label: `People Said / 人から言われたこと`
- Muted plum semantic marker.
- Quote/paraphrase/inference must be identified with explicit text labels or badges.
- Do not use quotation styling to imply that a paraphrase or inference is a verified direct quote.
- Speaker identity and publication state remain separate concerns from visual styling.

### Timeline

- Date/time is the organizing axis.
- Mixed artifacts should read as one chronological stream rather than a dashboard of unrelated cards.
- Content type is communicated by label + structure + semantic marker, never color alone.

## 4. Typography

### Font roles

```css
--font-body: "Noto Sans JP", "Hiragino Sans", "Yu Gothic", system-ui, sans-serif;
--font-heading: "Noto Sans JP", "Hiragino Sans", "Yu Gothic", system-ui, sans-serif;
--font-mono: ui-monospace, "SFMono-Regular", Consolas, monospace;
```

Do not add a remote font dependency solely to obtain a branded look. A future heading face may be introduced only if loading, Japanese fallback, and layout shift are controlled.

### Type scale

- Body prose: `1rem`–`1.0625rem` (16–17px at the default root size)
- UI controls: `0.875rem`–`1rem`
- Metadata/sub-labels: never below `0.75rem` (12px)
- Page heading: fluid, but normally capped near `3rem`
- Long-form line-height: `1.85`–`2`
- UI line-height: `1.4`–`1.6`

Japanese labels must not use exaggerated Latin-style tracking. Wide letter-spacing is reserved for short Latin eyebrow text where it materially improves hierarchy.

### Reading measure

- Main long-form prose: approximately `38rem`–`46rem` maximum width.
- Archive/list layout may be wider, but individual prose blocks should return to the reading measure.
- Do not enlarge hero typography at the expense of the first screen of readable content.

## 5. Spacing and layout

Use a 4px base unit with a restrained scale:

```text
4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48 / 64 / 80
```

### Canonical layout rules

- Main archive width: approximately `min(1080px, calc(100% - 32px))`.
- Long-form detail width: approximately `720px`.
- Desktop whitespace is intentional; do not fill it with KPI cards.
- Mobile defaults to one reading column.
- Image absence must collapse naturally without leaving decorative placeholders.
- At 200% text zoom, content and controls must remain available without two-dimensional scrolling for ordinary reading flows.

## 6. Surfaces, borders, and radius

- Canvas: warm neutral.
- Primary reading surface: white paper.
- Secondary/quiet surface: warm off-white.
- Borders are the primary method of separating interactive surfaces.
- Shadows are optional and extremely light; a border-only treatment is preferred.

Suggested radius scale:

```css
--radius-sm: 8px;
--radius-md: 12px;
--radius-lg: 16px;
```

Do not make every paragraph or timeline item a floating card. Group only when grouping carries meaning.

## 7. Interaction and motion

Canonical interaction feedback:

1. text/tone change
2. border change
3. background tint
4. motion only when it explains state

Do not use hover lift for standard archive items.

Suggested durations:

```css
--motion-fast: 120ms;
--motion-normal: 200ms;
--motion-slow: 320ms;
--ease-standard: cubic-bezier(0.4, 0, 0.2, 1);
```

`prefers-reduced-motion: reduce` must remove non-essential transitions and animations.

## 8. Focus and keyboard contract

Target conformance is **WCAG 2.2 Level AA** for the public Reader. In addition, KafLog adopts the measurable visual target from WCAG 2.2 Success Criterion 2.4.13 Focus Appearance (AAA) for author-defined focus indicators where practical:

- visible keyboard focus for every interactive control
- focus indicator area at least equivalent to a 2 CSS pixel perimeter
- focus-state contrast of at least 3:1 against the corresponding unfocused pixels
- focused controls must not be obscured by sticky/navigation UI

A standard implementation should prefer a real outline/border rather than glow-only focus styling.

Official references:

- https://www.w3.org/TR/WCAG22/
- https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html

## 9. Accessibility acceptance rules

For implementation PRs:

- normal text: at least 4.5:1 contrast
- large text: at least 3:1 contrast
- UI component/focus visual boundaries: verify applicable non-text contrast requirements
- keyboard navigation: no unreachable interactive element
- focus: always visible
- content type and state: never conveyed by color alone
- text resize/reflow: verify at 200% zoom and representative narrow viewport
- reduced motion: respected

Contrast must be checked on the actual rendered foreground/background pair, not inferred from a token name.

## 10. Representative visual-regression views

The implementation issue must stabilize screenshots for these views using deterministic public-only fixtures.

### Desktop

1. Home / archive entry point
2. Diary list
3. Diary detail with image
4. Diary detail without image
5. Novel list/detail
6. People Said with direct quote + paraphrase examples
7. Timeline containing multiple artifact types on the same date

### Mobile

1. Home
2. Diary detail
3. Timeline
4. Primary navigation selected/open state, if applicable

Snapshots are regression evidence, not a substitute for accessibility or production E2E checks.

## 11. Dark mode

Light editorial appearance is canonical.

A dark mode may exist later, but it must preserve the same semantic hierarchy and reading character. It must not revert to black + cyan neon, glow-heavy surfaces, or glassmorphism.

## 12. Implementation boundary

This document defines the visual contract. It does not change:

- canonical memory/evidence models
- publication/privacy decisions
- Social Mirror extraction
- Reader navigation information architecture

Those concerns remain in their dedicated issues. Visual implementation belongs to the follow-up Reader application issue.