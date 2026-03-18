---
name: Discord 通知設定（2026-03-18）
description: VLog で毎回 Discord に通知を送信するための設定完了
type: project
---

# Discord 通知セットアップ完了

## 実装内容
- **Webhook URL設定**: `.env` に `DISCORD_WEBHOOK_URL` を設定
- **自動通知**: `task process:daily` 完了時に Discord へ自動通知
- **テスト実行**: `uv run python -m src.cli notify --message "..."` で動作確認

## 設定方法
```bash
# .env に以下を追加
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN
```

## 既存の通知ポイント
- **task process:daily** (末尾): 日次処理完了時に通知送信
  - メッセージ例: `✅ 日次処理が完了しました（2026-03-18 03:00:00）`

## テスト方法
```bash
task setup  # .env が読み込まれる
uv run python -m src.cli notify --message "テストメッセージ"
```

## 注意
- Webhook URL は秘密情報なので `.env` は gitignore済み
- `.env.example` は テンプレート用（実際の Webhook URL は入力不要）
