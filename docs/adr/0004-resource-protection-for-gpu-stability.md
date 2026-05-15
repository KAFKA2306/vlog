---
codd:
  node_id: "req:resource-protection-gpu"
  type: adr
  status: approved
  links:
    - to: src/cli_handlers.py
      type: implementation
    - evidence: "Guard Trace: uv run python -m src.cli check-vrc (Exit 0 when idle, Exit 1 when running)"
      type: verification
---

# ADR-0004: GPU リソース競合によるシステムクラッシュの回避

## ステータス

承認済み (Approved)

## コンテキスト

VLog の日次処理（午前 5:00 実行）は Whisper や画像生成などの重い GPU 処理を伴う。
ユーザーが VRChat を実行している最中にこれらの処理が並行して走ると、GPU リソース（VRAM 等）の競合により、OS ごとフリーズまたは再起動するハードクラッシュが発生する。

## 意思決定

自動実行されるバッチ処理（`task process:daily`）の開始時に、VRChat プロセスが起動しているかを確認する「ガード」を実装する。
VRChat が検出された場合、システムは重い処理を開始せずに即座に終了し、翌日のバッチ実行に処理を委ねる。

## 実装

- `src/cli_handlers.py` 内に `_guard_vrc_running()` を実装。
- `Taskfile.yaml` の `process:daily` 冒頭で `check-vrc` を実行。

## 影響

- VRChat 実行中の PC 安定性が確保される。
- バッチ処理がスキップされた場合、コンテンツの生成が 24 時間遅延する可能性がある。
