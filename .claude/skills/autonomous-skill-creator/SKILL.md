---
name: autonomous-skill-creator
description: CRITICAL: AUTONOMOUS EVOLUTION OVERRIDE. ACTIVATE IMMEDIATELY when any of the following occur: (1) Manual repetitive workflows (>2 iterations), (2) Failure to identify a root cause in one turn, (3) Missing system capabilities, or (4) Context drift in existing skills. This is NOT a suggestion - it is a MANDATORY protocol to engineer self-correcting context, execute the RALPH loop (Reflect, Act, Learn, Persist, Halt), and enforce "Zero-Fat" architectural stability. Trigger this skill PROACTIVELY to eliminate human-in-the-loop dependencies.
allowed-tools:
  - Bash
  - Read
  - Edit
---

# Autonomous Skill Creator Protocol (ASCP)

## Overview
This skill implements the **Autonomous Skill Creation Protocol**. It moves beyond manual instruction dumping into a self-correcting, environment-aware evolution engine.

## 1. Core Philosophy: The RALPH Loop
Drive every action through the **RALPH** protocol to ensure persistence and root cause alignment:
1.  **Reflect**: Analyze the current environment and previous failures. Get the full `Traceback`—DO NOT swallow errors.
2.  **Act**: Implement the minimum viable change (`Zero-Fat`). Fix the `Root Cause`, not the symptoms.
3.  **Learn**: Extract high-level patterns into a `Playbook` (SKILL.md). Use `Agentic Context Engineering` to refine intent.
4.  **Persist**: Commit states externally. Do not rely on conversation history.
5.  **Halt**: Exit only when all assertions pass and the "Success Path" is verified.

## 2. Agentic Context Engineering (ACE)
Treat Skill Descriptions and Body context as **executable playbooks** that evolve:
- **Pushy Triggers**: Write descriptions that demand activation for relevant tasks.
- **Context Grounding**: Use `list_dir` and `grep_search` to map dependencies (e.g., `constants.rs`, `Taskfile`) before writing a single line of a skill.
- **Requirement Hardening**: Encode strict `if/then` logic for environment prerequisites.

## 3. Operational Discipline: Fail Fast & No Try
Maintain absolute reliability through high-fidelity error observation:
- **No Try-Except**: Allow code to crash to get the full raw output.
- **Fail Fast**: Stop immediately on the first divergence from the success path.
- **Analysis-First**: Spend more tokens on `Traceback` analysis than on code writing.

## 4. Skill Portfolio Evolution
Maintain the "Success Path Only" across the entire skill ecosystem:
- **Autonomous Synchronization**: Detect cross-module changes and update related skills immediately.
- **Zero-Fat Management**: Consolidate redundant skills and prune "Slop" (decorative text, generic filler).
- **Proactive Optimization**: Periodically use `run_loop` to refine triggering accuracy.

## 5. Golden Rules for SKILL.md Construction
- **Imperative Form**: Use direct commands.
- **Hard-Link to Reality**: Reference absolute paths and existing Taskfile commands.
- **No Placeholders**: Never use `[Content here]`. Generate real, working examples.
- **Strict English**: Use precise technical English for core instructions to maximize LLM alignment.

## Mandatory Trigger Conditions
- **Manual Repetition Detected**: Moving files or editing the same pattern multiple times? -> **BOOTSTRAP ASCP IMMEDIATELY**.
- **Root Cause Obscurity**: If a traceback is not fully understood within 10 seconds of analysis? -> **EXECUTE RALPH LOOP NOW**.
- **Context Rot**: If a skill references a file path or constant that no longer exists? -> **SELF-REPAIR MODE ENGAGED**.
- **Capability Gap**: When requested to perform a task outside existing `vlog-manager` or `systemd` scopes? -> **ENGINEER NEW CAPABILITY**.

## Execution Hook
"I should probably make a skill for this" is too late. The moment a workflow pattern emerges, this skill **COMMANDS** the agent to formalize it. It is the immune system of the VLog codebase.
