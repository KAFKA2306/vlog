# AGENTS.md

VRChat Auto-Diary (vlog) 開発用エントリーポインタ。

## 🎯 プロジェクト概要
VRChatの活動を自動監視・録音し、Geminiで要約・小説化して記録するライフログシステム。

## 📍 主要ポインタ
詳細なルールとワークフローは以下を参照：

- **コーディング規約**: [.claude/rules/python_coding.md](file:///home/kafka/projects/vlog/.claude/rules/python_coding.md) / [.claude/rules/general.md](file:///home/kafka/projects/vlog/.claude/rules/general.md)
- **コマンド・手順**: [.claude/rules/commands.md](file:///home/kafka/projects/vlog/.claude/rules/commands.md) / [Taskfile.yaml](file:///home/kafka/projects/vlog/Taskfile.yaml)
- **アーキテクチャ定義**: [docs/architecture.md](file:///home/kafka/projects/vlog/docs/architecture.md)
- **意思決定履歴**: [docs/adr/](file:///home/kafka/projects/vlog/docs/adr/)

## 🚀 クイックコマンド
エージェントは常に以下のツールを使用して作業を検証すること：

```bash
task lint    # 保存後に自動実行される（PostToolUse）
task status  # システム全体の稼働状況確認
task dev     # ローカル実行テスト
```

## ⚠️ 禁止事項
- **設定ファイルの直接編集禁止**: `.claude/settings.json`, `pyproject.toml` 等はハーネスにより保護されている。
- **ドキュメントの肥大化禁止**: 新しいルールは `.claude/rules/` に追加し、`AGENTS.md` は軽量に保つ。
