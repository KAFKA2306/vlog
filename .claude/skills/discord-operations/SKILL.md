---
name: discord-operations
description: VLogプロジェクトにおけるDiscord通知、Webhook連携、およびサービス監視を管理するスキル。日次処理の成功・失敗通知やsystemdの状態監査を担当する。
type: skill
---

# Discord Operations (VLog Edition)

## Objective

VLogシステムの稼働状況や日次処理の結果をDiscordチャンネルへ確実に通知し、異常を早期に検知するための通信・監視を管理する。

## Essential Paths

- Configuration: `data/config.yaml` (whisper, gemini等のモデル設定含む)
- Environment Variables: `.env` (`DISCORD_WEBHOOK_URL` を保持)
- Implementation: `src/cli.py` / `src/cli_handlers.py` (notifyコマンドの実装)
- Systemd Units: `vlog.service`, `vlog-daily.service`, `vlog-daily.timer`, `vlog-daily-failure.service`

## Key Functions

### 1. Alert Notifications (`task notify`)
`src.cli notify` コマンドを使用して、リアルタイムの通知を送信する：
- **info**: 録音開始、システム起動などのマイルストーン。
- **success**: 日次処理の完了、小説・画像生成の成功。**MUST** include Vercel URL (https://kaflog.vercel.app).
- **warn**: 一時的なAPIエラー、VRChat実行中によるHEAVY処理のスキップ。
- **error**: 致命的なクラッシュ、ディスク容量不足、通知サービス (`vlog-daily-failure.service`) による自動報告。

### 2. Failure Handling
`vlog-daily-failure.service` を通じた自動通知：
- `vlog-daily.service` が失敗した際に自動起動し、失敗時刻とエラー発生を報告する。

## System Audits

以下のチェックを実行してシステムの健全性を監査する：
1. **systemd Verification**: `systemctl --user is-active vlog.service vlog-daily.timer` を確認。
2. **Connectivity Validation**: `.env` 内の `DISCORD_WEBHOOK_URL` が有効なDiscord Webhook URLであることを確認。
3. **Log Audit**: `journalctl --user -u vlog-daily-failure.service` を確認し、過去の失敗通知が正常に送信されているかを確認。
