# VLog 日次実行とロギング (必須)

## 概要

VLog は毎日 **03:00 JST** に自動実行されます。実行結果は複数の場所に記録されます。

## 実行スケジュール

```
Timer:   vlog-daily.timer (03:00 JST 毎日)
Service: vlog-daily.service
          ├─ ExecStartPre:  ログ開始記録
          ├─ ExecStart:     task process:daily 実行
          └─ ExecStartPost: ログ完了記録
```

**次回実行**:
```bash
systemctl --user list-timers vlog-daily.timer
```

## ロギング場所と内容

### 1. systemd journal (永続)

**24時間以内の実行ログ**:
```bash
journalctl --user -u vlog-daily.service --since "24 hours ago"
```

**最新10件**:
```bash
journalctl --user -u vlog-daily.service -n 10
```

**リアルタイム監視** (テスト用):
```bash
journalctl --user -u vlog-daily.service -f
```

### 2. 操作ログ (`/tmp/vlog-daily.log`)

人間可読形式: タイムスタンプ + 実行状態

```bash
# 全体表示
task log:daily

# 直近20行
tail -20 /tmp/vlog-daily.log
```

**例**:
```
[2026-03-19 03:00:01] vlog-daily.service starting...
[2026-03-19 03:07:34] vlog-daily.service completed ✅
```

## 日次チェック手順

### 毎朝の確認 (推奨時間: 朝 7:00)

```bash
# ワンコマンドで全確認
task health:check
```

出力例:
```
■ Timer Status
✅ Timer: ACTIVE

■ Latest Run Result
✅ Last run appears successful
Mar 19 03:07:34 DESKTOP-SMJEQON systemd[4002]: Starting VRChat Vlog Daily Processing...

■ Supabase Sync Status
✅ Supabase: ACCESSIBLE
```

### 詳細ログ確認

```bash
# 実行ログの詳細
task monitor:daily

# Supabase 同期の詳細確認
task sync

# コンテンツ生成の確認
ls -ltr data/novels data/summaries data/photos | tail -5
```

## 失敗時の対応

### シナリオ 1: Supabase が一時停止している

**症状**:
```
❌ Last run may have failed
⚠️  Supabase: PAUSED or UNREACHABLE
```

**対応**:
1. https://supabase.com/dashboard にアクセス
2. **KafLog** プロジェクト → **Resume project** をクリック
3. 2-3 分待機
4. `task sync` で確認

### シナリオ 2: タイマーが実行されていない

**症状**:
```
❌ Timer: INACTIVE
```

**対応**:
```bash
# 再度有効化
systemctl --user enable --now vlog-daily.timer

# 確認
systemctl --user status vlog-daily.timer
```

### シナリオ 3: サービスプロセスがクラッシュしている

**症状**:
```
❌ Last run may have failed
journalctl に "exited, code=..." が表示
```

**調査**:
```bash
# 直近のエラーメッセージ
journalctl --user -u vlog-daily.service -n 20 | grep -i "error\|failed"

# Python トレースバック（あれば）
journalctl --user -u vlog-daily.service --since "2 hours ago" | tail -50
```

## ログ管理

### ログファイルのクリア (週1回推奨)

```bash
task log:clear
```

この後、新しい週のログが `/tmp/vlog-daily.log` に書かれます。

### ログ保管ポリシー

| ログ | 場所 | 保管期間 | 管理 |
|------|------|--------|------|
| systemd journal | 自動 | 1-4 週 | システム自動管理 |
| 操作ログ | `/tmp/vlog-daily.log` | 手動削除まで | `task log:clear` で定期削除 |
| データファイル | `data/` | 無期限 | Git で管理 |

## 警告フラグ

毎日のチェックで以下を確認してください:

- ✅ **Timer は ACTIVE か**: 有効化されていないと実行されない
- ✅ **Last run は successful か**: 失敗が続いている場合は調査
- ✅ **Supabase は ACCESSIBLE か**: PAUSED の場合は再開が必要
- ✅ **data/ に新しいファイルが生成されているか**: novels/, summaries/ をチェック

## 自動通知

サービスが失敗すると:
1. Discord webhook で通知 (設定済みの場合)
2. `/tmp/vlog-daily.log` に失敗記録
3. systemd journal に詳細ログ

## 緊急時の手動実行

テストや緊急時に即座に実行:

```bash
# 同期なし (高速)
task process:today

# 全処理 (Supabase と同期)
task process:daily

# 過去日付の処理
task process:yesterday
task novel:build date=20260318
```

## トラブルシューティング

**Q: 毎日自動実行されているか確認したい**
```bash
task monitor:daily
```

**Q: ログが見つからない**
- `/tmp/vlog-daily.log` は `/tmp` に保存 (volatile)
- systemd journal に確実に残る: `journalctl --user -u vlog-daily.service`

**Q: Supabase が一時停止したかどうか確認したい**
```bash
task sync
# "Could not find table" が出れば Supabase が paused
```

**Q: 次回実行がいつか確認したい**
```bash
systemctl --user list-timers vlog-daily.timer
```
