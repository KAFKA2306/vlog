---
name: zero_fat_cleanup
description: Automated detection and removal of code violations (try-catch, comments, docstrings, retry logic, unused code). ACTIVATE this skill whenever the code feels cluttered, redundant, or complex. Use it proactively before any commit or after any significant refactoring to enforce the "Iron Rules" of the project.
---

# Zero-Fat Cleanup (Skill)

ACTIVATE this skill to ruthlessly purge your codebase of any and all "fat."

## Core Principles
- **No Comments**: If you see a comment (`#`), DELETE IT.
- **No Docstrings**: If you see a docstring (`"""`), DELETE IT.
- **No Try-Catch**: If you see a `try-except`, REFACTOR IT into a direct call or let it crash.
- **No Retries/Timeouts**: If you see a `retry` or `timeout`, DELETE IT and fix the root cause.
- **No Unused Code**: If you see an unused function, variable, or import, DELETE IT.

## Operational Workflow
1. **Detect**: Scan the provided files for any of the above violations.
2. **Refactor**: Remove all identified fat and ensure the code remains functional.
3. **Verify**: Run `task lint` to ensure the clean code still adheres to the project's formatting and quality standards.

## Guidelines
- **Minimalism**: Small, composable functions are better than large, complex ones.
- **Pure Code**: Let the code speak for itself through type hints and clear naming.
- **Fast Execution**: Less code means faster analysis and fewer bugs.
