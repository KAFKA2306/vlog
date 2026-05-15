---
codd:
  node_id: "req:prompt-vault-integration"
  type: adr
  status: approved
  links:
    - to: scripts/sync_vault_prompts.py
      type: implementation
    - to: data/prompts.yaml
      type: configuration
---

# ADR-0005: Prompt Vault をソースオブトゥルースとするプロンプト管理

## ステータス

承認済み (Approved)

## コンテキスト

VLog プロジェクトにおける画像生成やキャラクター（Kafka）の描写において、プロンプトの一貫性と品質管理が重要である。
一方で、キャラクターのアイデンティティ定義や過去の成功事例（アセット）は別プロジェクト `prompt-vault` で集中的に管理・監査（Audit）されている。
`vlog` 内にプロンプトをハードコードしたり個別に管理すると、キャラクター設定の乖離（Identity Drift）や、最新のプロンプト改善の反映漏れが発生するリスクがある。

## 意思決定

`prompt-vault` を「プロンプトのソースオブトゥルース（信頼できる唯一の情報源）」として位置づけ、`vlog` のプロンプト設定をこれと同期する仕組みを導入する。
単なるテキストのコピーではなく、キャラクターのアイデンティティ（Identity）と視覚スタイル（Visual Style）を固定するための「ガード」を機械的に注入することを決定した。

## 実装

- **同期スクリプト**: `scripts/sync_vault_prompts.py` を実装。
  - `prompt-vault/db/prompts.json` から `character_kafka`, `kafka_identity_lock` に加え、`master_style_lighting` などのスタイル・ブロックも抽出。
  - アイデンティティ保持のための強力な記述（Consistency Guard）と、実写化を防ぐネガティブ・プロンプトの自動強化を実装。
- **タスク自動化**: `Taskfile.yaml` に `task vault:sync` を追加。
- **ドキュメント**: `AGENTS.md` に外部連携としてのリンクを明記。

## 影響

- **アイデンティティの固定**: 定義文だけでなく「一貫性維持の指示」が注入されるため、モデルの逸脱（Identity Drift）が抑制される。
- **スタイルの一貫性**: プロンプト・レベルでアニメ調の質感がロックされ、実写寄りの質感が生成されるリスクが低減する。
- **運用フローの確立**: `prompt-vault` 側でのプロンプト改善が、ワンコマンドで `vlog` の全生成パイプラインに波及する。
