---
name: agent-sync-manager
description: Manage and synchronize agent settings, skills, and configuration across the project. Use this skill when updating .claude/ or .gemini/ settings, managing skill deployments, or verifying sync status.
---

# Agent Sync Manager (Skill)

ACTIVATE this skill whenever changes are made to the `.claude/` or `.gemini/` directories, or when ensuring that the latest agent workflows and rules are correctly applied.

## Core Responsibilities
- **Config Sync**: Ensure `CLAUDE.md`, `GEMINI.md`, and local settings are consistent.
- **Skill Deployment**: Handle the copying and updating of skills across environments.
- **Status Verification**: Confirm that the agent's runtime environment matches the project's requirements.

## Commands
- `task sync:skills`: Synchronize skills from the master repository to the local project.
- `task sync:config`: Update project-specific configurations.
