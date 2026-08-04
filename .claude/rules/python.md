---
paths:
  - "apps/capture-vrchat/src/**/*.py"
  - "packages/**/*.py"
  - "scripts/**/*.py"
  - "tests/**/*.py"
  - "infra/systemd/**/*.py"
---

# Python rules

- Target the Python version declared in `pyproject.toml`.
- Use type hints for public contracts and non-trivial functions.
- Keep domain code independent from provider SDKs and applications.
- Preserve useful docstrings, comments, exception context, and structured logging.
- Catch exceptions only at a boundary that can add context, recover safely, translate the error, or perform cleanup.
- Use tests for invariants, regressions, and failure paths.
- Run `task lint` and `task test`; inspect formatting changes before staging.
