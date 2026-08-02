# VLog Operations

VLog の録音監視、文字起こし、生成、同期、通知、systemd 実行を、同一の構造化イベントで監査するための運用手順です。

## 目的

従来の `data/logs/vlog.log`、`data/daily_runs.jsonl`、systemd journal は、実行基盤ごとに分断されていました。録音開始失敗やバックグラウンド処理例外は、プロセス自体が生きている限り見落とせる構造でした。

本実装では以下へ統合します。

- `data/error_events.jsonl`: append-only の構造化イベント
- `data/heartbeats/vlog-service.json`: 常駐監視の最新 heartbeat
- `data/reports/operations.html`: 90 日監査のローカル HTML コックピット
- `data/reports/operations.json`: 機械可読の監査結果

ログはローカル専用です。API キー、Webhook、Bearer token、ホームディレクトリは保存前にマスクします。

## 初回反映

```bash
bash scripts/install_systemd_units.sh
```

このスクリプトは unit を再リンクし、`daemon-reload`、タイマー再起動、常駐サービス再起動、doctor、90 日レポート生成まで実行します。

## 日常操作

```bash
# 依存・unit 定義・秘密情報設定を診断
uv run python -m src.operations doctor

# 過去 90 日を集計し、HTML と JSON を生成
uv run python -m src.operations report --days 90 --open

# コンソールだけで確認
uv run python -m src.operations report --days 90
```

レポートは同一 `category / component / operation` の失敗をまとめます。最後の失敗より後に成功イベントがあれば「解消済み」、なければ「未解消」と判定します。

## 観測対象

| 分類 | 主な検出対象 |
|---|---|
| monitoring | VRChat プロセス検出失敗、常駐ループ例外、heartbeat 欠落 |
| recording | 録音開始失敗、録音スレッド死、停止失敗、空録音 |
| transcription | Whisper 実行失敗、成果物欠落 |
| processing | セッション処理例外、厳格監査失敗 |
| generation | Gemini 429、要約・小説・画像生成失敗 |
| sync | Supabase 同期失敗、反映検証失敗 |
| notification | Discord 通知失敗 |
| scheduler | systemd unit 失敗、起動バイナリ不整合 |
| infrastructure | 設定不足、ログ破損、書込不能 |

## 過去ログの扱い

レポート生成時には、次の既存ログも読み込みます。

- `data/incidents.jsonl`
- `data/daily_runs.jsonl`
- `data/logs/vlog.log`

旧テキストログの `429 / RESOURCE_EXHAUSTED` は Gemini rate limit、`/snap/bin/task` または `task: not found` は scheduler binary missing として分類します。

構造化ログ導入前の録音開始漏れは、成功・失敗の両方が記録されていないため、過去件数を厳密には復元できません。導入後は開始、停止、空録音、録音スレッド死を明示的に記録します。

## systemd 失敗時

`vlog.service` と `vlog-daily.service` の `OnFailure` は `src.operations service-failure` を呼び、以下を `error_events.jsonl` へ保存します。

- unit 名
- `Result` / `ExecMainStatus` / `ExecMainCode`
- 直近 40 行の journal

その後 Discord へ短い通知を送ります。詳細ログそのものは Discord や公開 Reader へ送信しません。
