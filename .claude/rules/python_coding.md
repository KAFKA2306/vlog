# Coding Rules & Principles

## Python Implementation

- **Python 3.11+**, type hints everywhere.
- 4-space indentation.
- `snake_case` (functions/modules), `PascalCase` (classes), `UPPERCASE` (constants).
- **Silent Operator**: No comments, no docstrings.
- **Zero-Fat**: 
    - No try-except blocks (crash on failure).
    - No retry/timeout logic.
    - No raw dicts; use Pydantic models in `src/models.py`.
- **Success Path Only**: Keep infrastructure/repositories minimal.

## Linting & Formatting

- Tool: `ruff`
- Command: `uv run ruff check src` & `uv run ruff format src`

## Directory Structure Enforcement

- `src/domain/`: Entities & Interfaces.
- `src/use_cases/`: Core logic.
- `src/infrastructure/`: Port implementations.
- `src/models.py`: Shared data models.
- **Avoid root file creation**.
