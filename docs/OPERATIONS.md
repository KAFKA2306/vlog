# VLog Operations

VLog の録音監視、文字起こし、生成、同期、通知、systemd 実行を、同一の構造化イベントで監査するための運用手順です。公開 Reader には運用ログを出しません。

## 運用モデル

監視は二層です。

1. WSL 内では `systemd` の `Type=notify` と `WatchdogSec=120s` が常駐プロセスの停止・ハングを検知します。
2. Windows Task Scheduler は 5 分ごとに systemd 状態と heartbeat 鮮度を確認し、WSL 側の監督機構ごと止まった場合に再起動します。

主なローカル成果物は次のとおりです。

- `data/error_events.jsonl`: 現在の構造化イベント
- `data/error_events.jsonl.1` 以降: サイズローテーションされた過去ログ
- `data/heartbeats/vlog-service.json`: 常駐監視の最新 heartbeat
- `data/reports/operations.html`: ローカル HTML コックピット
- `data/reports/operations.json`: 機械可読の監査結果

## 初回反映

WSL で実行します。

```bash
cd /home/kafka/projects/vlog
git pull --ff-only
bash scripts/install_systemd_units.sh
```

Windows 外形監視も有効化する場合は、通常権限の PowerShell で実行します。

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts/windows/install-vlog-watchdog.ps1
```

登録名は `VLog External Watchdog` です。ログは `%LOCALAPPDATA%\VLog\watchdog.log` に保存されます。

## インシデントの単位

障害は次の組み合わせで集約します。

```text
fingerprint + resource_id
```

`fingerprint` は分類、コンポーネント、操作、エラーコード、正規化したエラー内容から生成します。`resource_id` は音声入力、録音セッション、日次ステージ、systemd unit など、障害対象を表します。

通常の `succeeded` イベントでは障害を閉じません。対象障害の fingerprint を `resolves_fingerprint` で明示的に参照する `recovered` イベントだけが解消証跡になります。これにより、別マイク、別録音、別日次実行の成功による誤解消を防ぎます。

手動確認後に閉じる場合は次を使います。

```bash
uv run python -m src.operations recover-latest \
  --category recording \
  --component audio-recorder \
  --operation start \
  --resource-id audio-input:default \
  --message "Audio input was verified manually"
```

## ログの耐久性と保持

構造化イベントは次の保護を適用します。

- プロセス間ファイルロック
- 部分書き込みを許容しない write loop
- failure / recovered / critical のみ既定で `fsync`
- 既定 10 MiB でローテーション
- 既定 7 世代
- 既定 90 日保持
- API key、token、Webhook、ホームパスの保存前マスク
- 例外型、例外メッセージ、スタックトレース
- `service.name`、`service.instance.id`、`trace_id`、`span_id` 用フィールド

環境変数で変更できます。

```dotenv
VLOG_EVENT_MAX_BYTES=10485760
VLOG_EVENT_BACKUPS=7
VLOG_EVENT_RETENTION_DAYS=90
VLOG_EVENT_FSYNC=failures
```

`VLOG_EVENT_FSYNC` は `always`、`failures`、`never` のいずれかです。

## 日常操作

```bash
# 依存、unit、watchdog、ログ保持設定を診断
uv run python -m src.operations doctor

# 過去 90 日を集計して開く
bash scripts/open_operations.sh 90

# systemd と heartbeat を確認
systemctl --user status vlog.service
cat data/heartbeats/vlog-service.json

# Windows watchdog の直近ログ
powershell.exe -NoProfile -Command 'Get-Content "$env:LOCALAPPDATA\VLog\watchdog.log" -Tail 30'
```

## 録音監視

`AudioRecorder.start()` は音声ストリームが実際に開くまで最大 10 秒待機します。録音スレッド内で起きた例外は親ループから参照可能であり、無音のまま「録音中」と誤認しません。

検出対象は次のとおりです。

- 入力ストリーム開始失敗
- 開始タイムアウト
- 入力 overflow
- VRChat 稼働中の録音スレッド終了
- 停止タイムアウト
- 空または極端に小さい録音
- セッション処理失敗
- Supabase 同期失敗

## 過去ログ

レポートは次も読み込みます。

- `data/incidents.jsonl`
- `data/daily_runs.jsonl`
- `data/logs/vlog.log`

旧ログの `429 / RESOURCE_EXHAUSTED` は Gemini rate limit、`/snap/bin/task` または `task: not found` は scheduler binary missing として分類します。破損 JSONL 行は捨てず、`invalid_jsonl` インシデントとして可視化します。

構造化ログ導入前の録音開始漏れは、成功・失敗の双方が記録されていないため件数を厳密には復元できません。

## systemd 失敗時

`vlog.service` と `vlog-daily.service` の `OnFailure` は、unit の終了状態と直近 40 行の journal を `error_events.jsonl` へ保存します。その後に短い Discord 通知を送ります。journal、API key、Webhook は公開 Reader や通知本文へ転送しません。

## 検証

CI とローカルテストでは次を検証します。

- 通常成功で障害が誤解消されないこと
- fingerprint と resource が一致した明示 recovery だけが閉じること
- 複数プロセス同時書き込みで JSONL が破損しないこと
- ローテーション後もイベントが読めること
- 秘密情報と例外 stacktrace の処理
- 破損 JSONL の可視化
- systemd notify datagram
- Gemini 429 と旧 scheduler path の分類
