# General repository rules

- Follow [AGENTS.md](../../AGENTS.md) and the canonical documentation index.
- Keep public OSS, private memory, raw evidence, derived artifacts, and public projections separated.
- Preserve comments and docstrings that explain contracts, invariants, hazards, or non-obvious decisions.
- Use typed, bounded error handling at external boundaries. Do not swallow exceptions or force success after a required failure.
- Use explicit timeouts and retry policies only where operations are safe and idempotent.
- Tests and mocks are valid when they verify contracts without pretending to prove live infrastructure behavior.
- Avoid unrelated root files and duplicated command or dependency inventories.
- Do not modify protected prompts or model identifiers without explicit user instruction.
