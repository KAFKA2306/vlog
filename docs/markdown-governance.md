# Markdown governance

## Purpose

Markdown is part of the executable repository contract. It must describe one clear authority, remain portable, and distinguish current behavior from target architecture and historical evidence.

## Ownership classes

| Class | Location | Rule |
|---|---|---|
| repository entry | `README.md`, `AGENTS.md` | concise orientation and routing |
| normative docs | `docs/` | architecture, operations, maintenance, contracts |
| component docs | component `README.md` | local boundary and entry points only |
| decisions | `docs/adr/` | immutable rationale plus explicit audit status |
| incidents | `docs/incidents/` | dated evidence; never current status |
| agent adapters | `.agent/`, `.claude/`, `.gemini/` | short wrappers around canonical docs |
| tool memory | `.serena/` | pointers only; no production status or private memory |

Generic tutorials, theme libraries, communication templates, and unrelated language-maintenance guides do not belong in this product repository.

## Content rules

- Each retained Markdown file has a defined owner and purpose.
- Commands come from `Taskfile.yaml`; dependencies and versions come from manifests.
- Current model selections come from configuration and consuming code.
- Generated narratives and illustrations are described as derived artifacts.
- Completion claims identify repository, CI, and environment evidence separately.
- Relative links must resolve in the repository.
- Personal home paths, drive-specific paths, file-scheme links, and secrets are prohibited.

## Validation

`task doc:check` enforces repository boundaries, required documents, local Markdown links, portable paths, H1 headings, and size limits for active agent instructions.

A passing check confirms repository consistency only. It does not verify external URLs or live infrastructure.
