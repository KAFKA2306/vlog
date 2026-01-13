---
name: cleanup
description: Remove unused code, comments, error handling. Use for "clean" or "simplify" requests.
---
Delete:
- Unused functions, classes, variables
- Comments, docstrings
- try-except blocks
- Retry/timeout logic

Keep:
- Used code only
- Type hints

After: run lint
