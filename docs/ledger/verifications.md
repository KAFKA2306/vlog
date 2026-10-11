<!-- GENERATED from schemas/ledger/star.yaml by scripts/generate_ledger.py. Do not edit. -->
# Verification ledger

Checks and the strongest evidence level a pass can establish. Results are not recorded here; see CI and environment evidence.

| Task | Covers | Evidence level on pass |
|---|---|---|
| `task lint` | Python ruff check and format check | CI-verified |
| `task typecheck` | Python type check | CI-verified |
| `task test` | pytest suite | CI-verified |
| `task python:contract` | supported Python range, pin, CI, and path agreement | CI-verified |
| `task doc:check` | repository boundaries, Markdown links, generated ledger freshness | CI-verified |
| `task systemd:verify` | systemd unit rendering and verification | CI-verified |
| `task web:build` | Reader typecheck, lint, and build | CI-verified |
