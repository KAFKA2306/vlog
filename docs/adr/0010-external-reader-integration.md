---
codd:
  node_id: "req:adr-0010"
  type: adr
  status: accepted
  links:
    - to: Taskfile.yaml
      type: implementation
    - to: .claude/skills/discord-operations/SKILL.md
      type: implementation
    - evidence: "rg -n \"kaflog\\.vercel\\.app|rule-scribe-games\\.vercel\\.app\" README.md docs/architecture.md apps/reader/README.md Taskfile.yaml .claude/skills/discord-operations/SKILL.md docs/adr/0010-external-reader-integration.md"
    ---


# ADR-0010: 通知システムへの外部リーダー（Vercel）連携の統合

## ステータス

承認済み (Accepted)

## コンテキスト

VLog システムによって生成された成果物（日記、小説、画像）は、Vercel 上でホストされている Reader 画面（https://kaflog.vercel.app）を通じて閲覧される。
しかし、これまでの通知システム（Discord Webhook）には以下の課題があった：

1. **成果物へのアクセシビリティ**: 処理完了の通知を受け取っても、Reader 画面へ移動するためにブラウザのブックマークや手動入力が必要であり、ユーザー体験が分断されていた。
2. **情報の断片化**: システムの「完了報告」と、実際の「閲覧体験」が紐づいておらず、生成されたコンテンツが即座に確認されないケースがあった。

## 意思決定

Discord 通知を単なる「ステータス報告」から「閲覧ゲートウェイ」へと進化させるため、全ての成功通知に外部リーダーへのリンクを統合する。

### 1. 通知内容の拡充

- `Taskfile.yaml` の日次処理完了通知（`process:daily`）に、Reader URL を標準で含める。
- アップデート完了や重要な処理の成功通知においても、関連する Vercel リンクを付与する。

### 2. スキル・ガイドラインの策定

- `discord-operations` スキルにおいて、`success` カテゴリの通知には **必ず Vercel URL を含める** という制約を定義する。
- 通知メッセージは絵文字（🌐, 🚀, ✅ 等）を活用し、視認性を高める。

### 3. プロダクション URL の固定

- Vercel のプロダクション URL (`https://kaflog.vercel.app`) を通知のソースオブトゥルースとして定義し、環境を問わず一貫したアクセス手段を提供する。

## 影響

- **メリット**:
  - 通知からワンクリックで最新の活動記録を確認でき、ユーザーのフィードバックループが高速化される。
  - VLog システムとフロントエンド（Reader）の統合感が向上する。
- **デメリット**:
  - URL が変更された場合、複数の通知箇所（Taskfile, Skills 等）を更新する必要がある。
