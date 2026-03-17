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

## 💡 ガイドラインと設計思想
- **設定ファイルの保護について**: `.claude/settings.json` や `pyproject.toml` 等は、システムの安定性を担保するハーネスとして意図的に保護されています。これらの変更が必要な場合は、影響範囲を考慮して慎重に評価してください。
- **ドキュメントの分散によるコンテキスト維持**: `AGENTS.md` が巨大化すると、LLMのコンテキスト領域を圧迫し要点が伝わりにくくなります。新しいルールが必要な場合は `.claude/rules/` に追加し、このファイルは軽量なポインタのリストとして機能させてください。
