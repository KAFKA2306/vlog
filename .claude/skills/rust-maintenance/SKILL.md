---
name: rust-maintenance
description: Maintain Rust code quality by running linters, formatters, and unit tests. Use this skill for ALMOST ANY modification to the Rust core, compiler errors, or when the user mentions "Zero-Fat" or "Iron Rules". Be proactive: if the code looks messy or tests are missing, trigger this skill to run `cargo fmt` and `cargo clippy`.
---

# Rust Maintenance Skill

ACTIVATE this skill for any Rust-based tasks. It ensures strict type safety and code cleanliness in the VLog ecosystem.

## Core Operations
- **Fmt**: Run `cargo fmt` to ensure the code is idiomatic and clean.
- **Lint**: Run `cargo clippy` to catch common mistakes and enforce best practices.
- **Check**: Run `cargo check` to verify the build without fully compiling.
- **Clean**: Run `cargo clean` if build artifacts are causing issues.

## Guidelines
- **Strict Typing**: Use the most expressive and safe Rust types available.
- **No Unsafe**: Avoid `unsafe` code at all costs.
- **Zero-Fat Compliance**: No comments, no docstrings, no try-catch (prefer `unwrap()` or direct crash).
