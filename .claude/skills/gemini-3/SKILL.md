---
name: gemini-3
description: Manage and optimize the use of Google's Gemini 3 series within the VLog project. ACTIVATE this skill whenever the user mentions "Gemini", "Model switching", "Prompt engineering", or wants to improve the quality of audio summaries and narratives.
---

# gemini-3

ACTIVATE this skill whenever the user mentions "Gemini", "Model switching", "Prompt engineering", or wants to improve the quality of audio summaries and narratives.

## Models
- **`models/gemini-3-flash-preview`**: The primary model used for summarizing, novelizing, and task parsing. It offers a large context window and high reasoning capabilities with low latency.

## Configuration
Model names and parameters are centrally managed in `data/config.yaml` under the `gemini` and `novel` sections.

- `gemini.model`: Configures the summarizer model.
- `novel.model`: Configures the novelizer model.
- `novel.max_output_tokens`: Sets the output limit for chapters.

## Usage Guidelines
- **Context Utilization**: Leverage Gemini's large context window (1M+ tokens) for cross-day analysis.
- **Prompt Engineering**: Use the structured templates in `data/prompts.yaml`. Avoid hardcoding prompts in the source code.
- **Model Switching**: If quality issues arise, verify the active model in `data/config.yaml` and `.env` (GOOGLE_API_KEY).
