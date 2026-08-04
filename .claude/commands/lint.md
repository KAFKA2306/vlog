# Lint

Run the repository quality task and inspect any formatting changes it produces:

```bash
task lint
git diff --check
git status --short
```

Use `task test` and `task doc:check` before completion. Do not use obsolete top-level source paths in fallback commands.
