---
name: vlog-best-practices
description: Apply the "Golden Rules" of VLog operation and maintenance. ACTIVATE this skill whenever the system experiences crashes (exit 101), corrupted data (0-byte files), or when handling large-scale (1000+) data processing. It enforces "Success Path Only" logic and "Anti-Entropy" data hygiene to ensure the long-term stability of the autonomous life-logger.
---

# VLog Best Practices

ACTIVATE this skill for all code modifications, bug fixing, and architecture decisions.

## 1. Zero-Fat Principles
- **No Try-Catch**: DO NOT use try-except blocks. Let it crash (Fail-Fast).
- **No Comments**: DO NOT add comments or docstrings. Code must be self-documenting through type hints.
- **No Retries**: DO NOT implement retry or timeout logic. Fix the root cause instead.
- **Success Path Only**: Focus solely on the happy path. Infrastructure should be simple and stable.

## 2. Infrastructure Rules
- **Configuration over Hardcoding**: Use `data/config.yaml` and `.env`.
- **Minimal Codebase**: Consistently delete unused functions, variables, and files.
- **Strict Types**: Always use Python 3.11+ type hints for all parameters and return values.

## 3. Data Integrity
- **Atomicity**: Ensure that file saving and processing are atomic where possible.
- **Archives**: Always archive raw recordings to `data/archives/` after successful processing.
- **Cleaning**: Regularly run `task clean` to remove build artifacts and cache.

## 4. Diagnostics
- Use `task status` and `task logs` to identify the failure point.
- If a crash occurs, trace the origin from the last successful log entry.
