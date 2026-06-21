---
codd:
  node_id: "req:adr-0011"
  type: adr
  status: accepted
  links:
    - to: vlog-daily.timer
      type: implementation
    - to: docs/MAINTENANCE.md
      type: implementation
    - to: docs/DAILY_MONITORING.md
      type: implementation
    - evidence: "rg -n \"09:00 JST|09:00:00|9AM JST\" vlog-daily.timer docs/MAINTENANCE.md docs/DAILY_MONITORING.md"
---

# ADR-0011: `vlog-daily.timer` の実行時刻を 06:00 から 09:00 JST に変更する

## ステータス

承認済み (Accepted)

## コンテキスト

`vlog-daily.timer` は、VLog の日次処理を自動起動する基盤である。
従来は毎朝 06:00 JST に実行されていたが、運用上の都合により 09:00 JST へ変更する必要があった。

## 意思決定

日次実行時刻を毎朝 09:00 JST に統一する。

この変更は以下に反映する。

1. systemd timer 定義
2. 運用手順ドキュメント
3. 日次監視手順ドキュメント

## 影響

- **メリット**:
  - 日次処理の開始時刻が運用手順と一致し、確認作業が単純になる。
  - 朝の監視・メンテナンス時刻を 09:00 JST に揃えられる。
- **デメリット**:
  - 旧 06:00 JST 前提の運用メモや記憶は更新が必要になる。

## 検証

- `systemctl --user list-timers vlog-daily.timer` で次回実行が 09:00 JST であることを確認した。
- `systemctl --user status vlog-daily.timer` で unit が loaded / active であることを確認した。
