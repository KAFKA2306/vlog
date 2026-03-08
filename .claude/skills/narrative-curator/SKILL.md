---
name: narrative-curator
description: Evaluate and improve the quality, tone, and consistency of generated narratives and audio summaries. ACTIVATE this skill whenever the user mentions "narrative", "diary", "novel", "summary", or asks about personae and content quality. Do not wait for an explicit request to audit; if the user is refining creative output or checking for logic gaps in logs, this skill MUST be used. It integrates deeply with `task curator:eval`.
allowed-tools:
  - "Bash(task *)"
  - Read
  - Edit
disable-model-invocation: true
argument-hint: "[date YYYYMMDD]"
---

# Narrative Curator Skill

A skill dedicated to ensuring the highest quality of AI-generated content within the VLog system. It focuses on narrative flow, persona preservation, and character consistency.

## Core Responsibilities

### 1. Quality Evaluation
Run the automated evaluation suite for specific dates.
- **cmd**: `task curator:eval date=YYYYMMDD`
- Analyze the output of the evaluation (pass/fail metrics) and identify areas for manual refinement.

### 2. Style and Tone Audit
Manually review generated files in `data/novels/` to ensure they match the established "Auto-Diary" aesthetic.
- Check if the persona remains consistent across multiple chapters.
- Verify that summaries accurately reflect the core events of the recorded sessions.

### 3. Content Refinement
Suggest or apply edits to `data/novels/*.md` or `data/summaries/*.txt` when the automated evaluation flags issues.
- Re-run `task novel:build` if summaries are updated to regenerate the narrative.

### 4. AI出力品質退行の診断

summaryやnovelが突然英語になった、トーンが変わった、などの退行が疑われる場合：

**Step 1: promptsへの変更を確認**
```sh
git log --oneline -- data/prompts.yaml
```
変更がなければ、コード側が原因。

**Step 2: コード変更を時系列で確認**
```sh
git log --oneline src/
```
退行開始日付付近のコミットを特定する。

**Step 3: Summarizerの実装差分を確認**
```sh
git show <hash> -- src/infrastructure/ai.py
```
`prompts[...]` の参照キーが変わっていないか確認する。

**Step 4: キー整合性を確認**
```sh
grep -n 'prompts\[' src/infrastructure/ai.py
grep -n '^\w' data/prompts.yaml
```
コードが参照するキーと `prompts.yaml` の実際のキーが一致しているか照合する。

> **既知の失敗パターン**: コードが `prompts["novel_generation"]` を参照しているが `prompts.yaml` にそのキーが存在しない場合、英語のハードコードフォールバック文字列が使われる。
> `data/prompts.yaml` は **PROTECTED FILE** — 明示的な指示なく変更禁止。

## Guidelines
- Follow the "Silent Operator" principle: keep edits concise and focused on narrative quality.
- Use the `media-expert` skill (if available) as reference for tone and image generation prompts.
- If backend synchronization is needed after regeneration, ask for explicit user confirmation before running `task sync`.

## Examples
- "Check consistency for yesterday's novel" -> `task curator:eval date=$(date -d "yesterday" +%Y%m%d)`
- "The summary is too short; make it more detailed" -> [Edit summary file] -> `task novel:build`
- "Make the diary tone gentler" -> [Modify system prompt or edit existing files]
- "Verify generated images match novel content" -> Use `task photos:fill` to backfill missing images and review alignment.
