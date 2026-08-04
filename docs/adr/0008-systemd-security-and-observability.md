---
codd:
  node_id: "req:adr-0008"
  type: adr
  status: accepted
  links:
    - to: infra/systemd/vlog.service.in
      type: implementation
    - to: infra/systemd/vlog-daily.service.in
      type: implementation
    - to: vlog-daily-failure.service
      type: implementation
    - evidence: "rg -n \"OnFailure=vlog-daily-failure.service|ProtectSystem=strict|NoNewPrivileges=yes|ReadWritePaths=|ReadOnlyPaths=\" infra/systemd/vlog.service.in infra/systemd/vlog-daily.service.in infra/systemd/vlog-daily-failure.service.in"
    ---


# ADR-0008: systemd サービスのセキュリティ強化と観測性の向上

## ステータス

承認済み (Accepted)

## コンテキスト

VLog システムは `systemd` を利用してバックグラウンドで活動を監視し、日次で大規模なデータ処理を行っている。しかし、従来のユニットファイルには以下の課題があった：

1. **セキュリティの不足**: サービスがユーザー権限で動作しているものの、サンドボックス化が行われておらず、ファイルシステムやネットワークへのアクセスが制限されていなかった。
2. **観測性の欠如**: `vlog-daily.service`（日次処理）が失敗した場合、ログを確認するまでその事実に気づくことができず、エラーの早期検知が困難であった。
3. **可搬性の低さ**: パスが特定のユーザーディレクトリにハードコードされており、環境移行時の柔軟性に欠けていた。

## 意思決定

systemd ユニットファイルを刷新し、セキュリティと信頼性を向上させる。

### 1. セキュリティ・ハードニングの導入

- `NoNewPrivileges=yes`: 子プロセスによる権限昇格を禁止。
- `PrivateTmp=yes`: サービス専用の独立した `/tmp` を提供。
- `ProtectSystem=strict`: OS 階層を読み取り専用に設定。
- `ProtectHome=read-only`: ホームディレクトリを原則読み取り専用とし、`ReadWritePaths` で必要なディレクトリ（`data/`, `logs/` 等）のみ書き込みを許可。

### 2. 失敗通知ハンドラの自動化

- `vlog-daily.service` に `OnFailure=vlog-daily-failure.service` を設定。
- `vlog-daily-failure.service` を新規作成し、失敗時に Discord Webhook 等を通じて即座に管理者へ通知を送信する仕組みを構築。

### 3. パス指定の一般化

- ハードコードされたユーザーパスを `%h` (User Home Specifier) に置き換え、環境依存性を低減。
- `uv` 等のバイナリパスを明示的に指定し、`PATH` 依存による実行失敗を防止。

## 影響

- **メリット**:
  - 万が一アプリケーションが侵害された際の影響範囲を最小限に限定できる。
  - 日次処理の失敗をリアルタイムで把握でき、データの欠落期間を短縮できる。
  - ユニット定義がプロジェクト内に集約され、構成管理が容易になる。
- **デメリット**:
  - 読み書きが必要なディレクトリを追加する際、ユニットファイルの更新が必要になる。
