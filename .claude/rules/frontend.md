---
paths:
  - "apps/reader/**/*.tsx"
  - "apps/reader/**/*.ts"
  - "apps/reader/**/*.css"
---

# Reader rules

- The application root is `apps/reader/`.
- Use the package manager and scripts defined by `apps/reader/package.json` and `bun.lock`.
- Preserve semantic HTML, keyboard access, visible focus, readable contrast, responsive layouts, and reduced-motion behavior.
- Do not expose private evidence or service-role credentials to the browser.
- Keep comments when they explain accessibility or non-obvious browser behavior.
- Run `task web:build` before completion.
