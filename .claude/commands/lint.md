Run lint and format:

```bash
task lint
```

Fallback if no Taskfile:
```bash
uv run ruff check src tests && uv run ruff format src tests
```
