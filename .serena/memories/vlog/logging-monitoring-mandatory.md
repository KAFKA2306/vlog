# VLog 日次自動実行 & ロギング (2026-03-18 実装)

## 実装内容

### systemd Service 強化
```
vlog-daily.service:
  - ExecStartPre:  ログ開始記録 → /tmp/vlog-daily.log
  - ExecStart:     task process:daily
  - ExecStartPost: ログ完了記録
  - StandardOutput/Error: journal (systemd 永続ログ)
```

### Taskfile モニタリングタスク
- `task monitor:daily` - 最新実行ログ + Timer状態 + 過去24h記録
- `task health:check` - Timer ACTIVE確認 + 最新実行結果 + Supabase状態
- `task log:daily` - /tmp/vlog-daily.log 全体表示
- `task log:clear` - ログクリア (週1回推奨)

### ロギング場所
1. **systemd journal** (永続): `journalctl --user -u vlog-daily.service`
   - 1-4週間保管
   - システム自動管理

2. **/tmp/vlog-daily.log** (易読形式):
   - 開始/完了/失敗を人間可読で記録
   - 次回実行時に追記
   - `task log:clear` で手動削除

## スケジュール
毎日 **03:00 JST** に自動実行
確認コマンド: `systemctl --user list-timers vlog-daily.timer`

## チェック方法
```bash
task health:check        # 日次確認（推奨朝7:00）
task monitor:daily       # 詳細ログ確認
journalctl --user -u vlog-daily.service --since "24 hours ago"
```

## 失敗時対応
- Supabase 一時停止: Resume ボタンクリック
- Timer 実行されない: `systemctl --user enable --now vlog-daily.timer`
- プロセスクラッシュ: journalctl で詳細確認
