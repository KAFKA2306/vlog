---
name: gemini-3
description: Manage and optimize Gemini usage for VLog summaries and narratives. ACTIVATE this skill whenever the user asks about Gemini config, model switching, prompt quality, summary quality regression, or cross-day long-context analysis. Always resolve model names from project configuration before recommending a switch.
user-invocable: false
allowed-tools:
  - Read
---

# Gemini 3 Skill

A skill to master the Gemini 3 lineup for high-fidelity life logging and narrative generation.

## Model Selection Guide

Use project configuration as source of truth. Do not hardcode model IDs in this skill.

1. **Default model**
   - Resolve from `src/domain/constants.rs` (`DEFAULT_GEMINI_MODEL`) and runtime settings.
   - For operational behavior, check `src/infrastructure/settings.rs` where `GEMINI_MODEL` env override is applied.

2. **When to switch**
   - Prefer higher-reasoning variants only when default quality is insufficient or multi-day analysis is requested.
   - Record the selected model in config/env rather than embedding ad-hoc names in prompts.

## Prompt Engineering for Gemini 3

### 1. Large Context Windows
- Gemini 3 supports 1M+ tokens. Don't be afraid to feed it multiple days of transcripts or entire code modules for cross-referencing.
- **Pattern**: "Based on the transcripts from the last 7 days (attached), identify repeating themes in my social interactions."

### 2. Systematic Instructions
- Use structured formats (Markdown, XML-like tags) for complex instructions.
- **Pattern**: 
  ```xml
  <instruction>Summarize the audio with a focus on emotional beats.</instruction>
  <context>User was in a high-intensity VRChat event.</context>
  ```

### 3. Reasoning
- For difficult debugging or temporal correlation tasks, request step-by-step analysis.
- **Pattern**: "Analyze the monitor logs from yesterday and explain, step by step, why the recording stopped early at 14:00."

## Project Configuration

- **Primary Setting**: `DEFAULT_GEMINI_MODEL` in `src/domain/constants.rs`.
- **Runtime Override**: `GEMINI_MODEL` in `.env` (resolved in `src/infrastructure/settings.rs`).

## Examples
- "Use a more accurate model for summaries" -> Check current model and propose a config-based switch.
- "Where is Gemini configuration?" -> Point to `src/domain/constants.rs` and `src/infrastructure/settings.rs`.
- "I want cross-day log analysis" -> Generate instructions for long-context analysis.
- "I need deep debugging support" -> Recommend a higher-reasoning model only when default quality is insufficient.
