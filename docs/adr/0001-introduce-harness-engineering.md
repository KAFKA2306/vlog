# ADR 1: Implement Harness Engineering

## Status
Accepted

## Date
2026-03-09

## Context
AI Agent（Claude Code, Codex等）による自律的な開発をスケールさせるため、プロンプトの指示だけに頼らない機械的な品質ゲート（ハーネス）が必要である。

## Decision
以下の Harness Engineering ベストプラクティスを導入する。

1. **指向性ポインタとしての `AGENTS.md`**: 詳細なルールを外部ファイル（`.claude/rules/`）に逃がし、`AGENTS.md` を軽量なポインタ形式にする。
2. **PostToolUse Quality Hooks**: ファイル編集のたびに `ruff` による自動リント・フォーマットを強制する。
3. **PreToolUse Safety Gates**: 設定ファイル（`pyproject.toml`, `Taskfile.yaml` 等）の保護。
4. **テストによる自己検証**: エージェントが自身の変更を検証するためのユニットテスト・E2Eテストの導入。

## Consequences
- エージェントの出力品質が安定し、回帰バグが早期に発見される。
- `AGENTS.md` のトークン消費が削減され、コンテキストの純度が向上する。
- 開発者は「コードを書くこと」から「ハーネスを整備すること」に注力できる。
