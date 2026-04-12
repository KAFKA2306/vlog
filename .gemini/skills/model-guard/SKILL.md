---
name: model-guard
description: Gemini CLI がモデル名・embedding名を勝手に変更することを防止するガードスキル。config.yaml やsettings.py のモデル関連フィールドに触れるタスクで自動適用される。
---

# Model Guard Skill

## 目的

LLMエージェントが知識カットオフや推論により、旧モデル名（gemini-2.5-flash, gemini-1.5-pro 等）を提案・適用してしまう問題を防止する。

## 現在の正規モデル名（config.yaml が唯一の定義元）

モデル名の変更はユーザーの明示的指示がある場合のみ許可される。
正規モデル名は `data/config.yaml` を参照して確認すること。

## 強制ルール

1. **読み取り義務**: モデル関連の変更前に `data/config.yaml` を必ず読み取り、現在値を確認する
2. **変更禁止**: ユーザーが明示的にモデル名を指定しない限り、一切変更しない
3. **提案禁止**: 「このモデルに変更すべき」等の提案を自発的に行わない
4. **フォールバック保護**: `src/infrastructure/settings.py` の `_DEFAULT_LLM_MODEL` は `config.yaml` から動的に読み込まれるため、直接編集しない

## 禁止パターン

- `gemini-2.5-flash` をフォールバックとしてハードコード
- `gemini-1.5-pro` 等の旧世代モデル名を提案
- embedding モデル名を `cognee.py` 内で無断変更
- `config.yaml` の `model:` 行を「最適化」や「アップグレード」名目で変更

## 検出トリガー

以下のファイルを変更する際にこのスキルが自動適用される：
- `data/config.yaml`
- `src/infrastructure/settings.py`
- `src/infrastructure/cognee.py`
- `src/infrastructure/ai.py`
