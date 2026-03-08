---
name: claude-expertise-bridge
description: The master controller for all domain-specific expertise and workflows located in .claude/skills/. MUST trigger for any task involving vlog automation, audio processing, frontend UI/UX, systemd maintenance, media pipelines, or any specialized logic defined in the project's expert skill manifests.
---

# Claude Expertise Bridge

This skill acts as a dynamic gateway to the project's established expertise. It ensures that Gemini CLI operates with the same high-standard protocols and specialized workflows defined for Claude Code, maintaining perfect synchronization between AI agents.

## Mandatory Execution Protocol

1. **Expertise Discovery**: When a task relates to any subdirectory in `.claude/skills/` (e.g., `vlog-manager`, `frontend-design`, `systemd-maintenance`), you MUST immediately identify the relevant domain.
2. **Knowledge Injection**: Execute `read_file` on the `SKILL.md` located within the identified `.claude/skills/` subdirectory before proceeding with any implementation or analysis.
3. **Absolute Authority**: Treat the instructions found in the discovered `SKILL.md` as the **ULTIMATE PROCEDURAL AUTHORITY**.
4. **Diagnostic Reflex**: If a command (e.g., `task sync`) fails with a Python Traceback, immediately inspect any configuration or YAML files mentioned in the error log (e.g., `data/prompts.yaml`). Prioritize fixing syntax errors over debugging logic.
5. **Resource Orchestration**: Directly utilize scripts, reference documents, or assets stored within the `.claude/skills/[domain]/` directories.
6. **Cross-Domain Synthesis**: If a task spans multiple domains, load all relevant skill manifests and synthesize the instructions.

## Performance Mandate

- **ZERO REDUNDANCY**: Do not reinvent workflows already defined in the expertise bridge.
- **PRECISION FIRST**: Always verify local protocols before taking action.
- **SYSTEM INTEGRITY**: Ensure every change aligns with the "Clean Architecture" and "Minimal Code" principles documented in the project's root `GEMINI.md` and the discovered expert skills.
