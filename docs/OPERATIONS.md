# VLog Operations

VLog の録音、文字起こし、生成、同期、通知、systemd 実行を、同一の構造化イベントで監査します。運用ログは公開 Reader へ出しません。

## 監視構成

監視は二層です。

1. WSL 内では `systemd` の `Type=notify` と `WatchdogSec=120s` が常駐プロセスの停止・ハングを検知します。
2. Windows Task Scheduler は 5 分ごとに systemd 状態と heartbeat 鮮度を確認し、WSL 側の監督機構ごと停止した場合にサービスを再起動します。

主なローカル成果物:

- `data/error_events.jsonl`: 現在の構造化イベント
- `data/error_events.jsonl.1` 以降: ローテーション済みログ
- `data/heartbeats/vlog-service.json`: 最新 heartbeat
- `data/reports/operations.html`: ローカル運用コックピット
- `data/reports/operations.json`: 機械可読監査結果

## 初回反映

WSL:

```bash
cd /home/kafka/projects/vlog
git pull --ff-only
bash scripts/install_systemd_units.sh
```

任意の Windows 外形監視:

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts/windows/install-vlog-watchdog.ps1
```

登録名は `VLog External Watchdog`、ログは `%LOCALAPPDATA%\VLog\watchdog.log` です。

## インシデントの単位

障害は `fingerprint + resource_id` で集約します。通常の `succeeded` イベントでは障害を閉じません。対象障害の fingerprint を `resolves_fingerprint` で明示的に参照する `recovered` イベントだけが解消証跡です。復旧後に同じ障害が再発した場合は再び未解消になります。

手動確認後に閉じる例:

```bash
uv run python -m src.operations recover-latest \
  --category recording \
  --component audio-recorder \
  --operation start \
  --resource-id audio-input:default \
  --message "Audio input was verified manually"
```

## ログ耐久性

構造化イベントには以下を適用します。

- プロセス間ファイルロック
- 部分書き込みを防ぐ write loop
- failure / recovered / critical の選択的 `fsync`
- 既定 10 MiB、7 世代、90 日保持
- API key、token、Webhook、ホームパスのマスク
- 例外型、メッセージ、stacktrace
- `service.name`、`service.instance.id`、`trace_id`、`span_id` 用フィールド

変更可能な環境変数:

```dotenv
VLOG_EVENT_MAX_BYTES=10485760
VLOG_EVENT_BACKUPS=7
VLOG_EVENT_RETENTION_DAYS=90
VLOG_EVENT_FSYNC=failures
```

## 日常操作

```bash
uv run python -m src.operations doctor
bash scripts/open_operations.sh 90
systemctl --user status vlog.service
cat data/heartbeats/vlog-service.json
```

## 録音監視

`AudioRecorder.start()` は音声ストリームが実際に開くまで最大 10 秒待ちます。録音スレッド内の例外は親ループへ伝達され、次を検出します。

- 入力ストリーム開始失敗・タイムアウト
- 音声入力 overflow
- VRChat 稼働中の録音スレッド終了
- 停止タイムアウト
- 空または極端に小さい録音
- セッション処理・Supabase 同期失敗

## 過去ログ

レポートは `data/incidents.jsonl`、`data/daily_runs.jsonl`、`data/logs/vlog.log` も読み込みます。旧ログの `429 / RESOURCE_EXHAUSTED` は Gemini rate limit、`/snap/bin/task` または `task: not found` は scheduler binary missing として分類します。破損 JSONL 行は `invalid_jsonl` インシデントとして可視化します。

## systemd 失敗時

`vlog.service` と `vlog-daily.service` の `OnFailure` は unit の終了状態と直近 40 行の journal をローカルログへ保存し、その後に短い Discord 通知を送ります。詳細ログや秘密値は通知・公開 Readerへ転送しません。

## 検証ゲート

Pull Request では、Python のコンパイル、Ruff lint・format、全 pytest を必須ゲートとして実行します。障害の誤解消、復旧後の再発、複数プロセス同時書き込み、ログローテーション、秘密値マスク、破損 JSONL、systemd notify を回帰テストで固定します。
