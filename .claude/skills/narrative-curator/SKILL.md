---
name: narrative-curator
description: Evaluate and improve the quality, tone, and consistency of generated narratives and audio summaries. ACTIVATE this skill whenever the user mentions "narrative", "diary", "novel", "summary", or asks about personae and content quality. Do not wait for an explicit request to audit; if the user is refining creative output or checking for logic gaps in logs, this skill MUST be used. It integrates deeply with `task curator:eval`.
---

# Narrative Curator Skill

A skill dedicated to ensuring the highest quality of AI-generated content within the VLog system. It focuses on narrative flow, persona preservation, and character consistency.

## Core Responsibilities

### 1. Quality Evaluation
Run the automated evaluation suite for specific dates.
- **cmd**: `task curator:eval date=YYYYMMDD`
- Analyze the output of the evaluation (pass/fail metrics) and identify areas for manual refinement.

### 2. Style and Tone Audit
Review generated files in `data/novels/` to ensure they match the established "Auto-Diary" aesthetic.
- Check if the persona remains consistent across multiple chapters.
- Verify that summaries accurately reflect the core events of the recorded sessions.

### 3. Content Refinement
Suggest or apply edits to `data/novels/*.md` or `data/summaries/*.txt` when the automated evaluation flags issues.
- Re-run `task novel:build` if summaries are updated to regenerate the narrative.

### 4. AI Outcome Diagnostic
If output quality regresses (e.g., summary becomes English, tone shifts):
- **Step 1**: Check `git log --oneline -- data/prompts.yaml` for prompt changes.
- **Step 2**: Check `git log --oneline src/` for code changes near the regression date.
- **Step 3**: Verify key consistency between `src/infrastructure/ai.py` (e.g., `prompts[...]`) and `data/prompts.yaml`.

## Guidelines
- Follow the "Silent Operator" principle: keep edits concise and focused on narrative quality.
- Use `data/prompts.yaml` as the source of truth for all AI instructions.
- If backend synchronization is needed after regeneration, run `task sync`.
