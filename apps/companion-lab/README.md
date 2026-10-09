# Companion Lab

Static public projection for GitHub Pages.

This UI demonstrates only:

- term observation counts;
- frequency/recency weighted sampling;
- kana-to-integer quantization;
- the 73-bit VRChat parameter shape.

It deliberately does not load VLog private evidence, transcripts, journals, people data, or credentials. Browser demo state stays in `localStorage` under `vlog.companion.demo.words.v1`.

Canonical implementation boundaries:

- domain math: `packages/companion/`
- VRChat UDP OSC: `adapters/vrchat-osc/`
- static view: `apps/companion-lab/`

GitHub Pages deployment is handled by `.github/workflows/companion-pages.yml`. Repository Pages must be enabled once with **Settings → Pages → Source: GitHub Actions** before deployment can occur.
