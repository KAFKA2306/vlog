---
paths:
  - "data/config.yaml"
  - "src/infrastructure/settings.py"
  - ".env"
---

# Model Name Protection (PROTECTED)

## 絶対禁止事項

- `data/config.yaml` 内の `model:` フィールドをユーザーの明示的指示なしに変更してはならない
- `src/infrastructure/settings.py` 内の `_DEFAULT_LLM_MODEL` をユーザーの明示的指示なしに変更してはならない
- `.env` にモデル名を追加・変更してはならない（モデル名は `config.yaml` が唯一の定義元）

## 単一定義源 (Single Source of Truth)

- LLMモデル名: `data/config.yaml` の各セクション (`gemini.model`, `novel.model`, `jules.model`)
- Embeddingモデル名: `src/infrastructure/cognee.py`
- Whisperモデル名: `data/config.yaml` の `whisper.model_size`
- 画像モデル名: `data/config.yaml` の `image.model`

## 変更プロトコル

モデル名変更が必要な場合：
1. ユーザーが明示的に新しいモデル名を指定する
2. `data/config.yaml` のみを変更する
3. `settings.py` のフォールバック値は `_DEFAULT_LLM_MODEL` 経由で自動追従するため変更不要
