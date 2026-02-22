# CUDA 環境仕様レポート (Protocol v8.0)

Context7 (MCP) の原則に基づき、現在の CUDA 実行環境のスペックと設定を整理しました。

## 1. 事実把握 (Facts/Specs)

- **GPU ハードウェア**: NVIDIA GeForce RTX 5070 Ti
- **VRAM**: 16,303 MiB (16GB)
- **CUDA バージョン**: 12.x (Driver API)
- **cuDNN バージョン**: 9.10.2 (Runtime via `nvidia-cudnn-cu12`)
- **主要ライブラリパス**:
    - CUDA Driver: `/usr/lib/wsl/lib/libcuda.so`
    - cuDNN Runtime: `/home/kafka/projects/vlog/.venv/lib/python3.13/site-packages/nvidia/cudnn/lib/`

## 2. 実装仕様 (Implementation)

### A. 動的ライブラリ注入
WSL 環境でのライブラリロードエラーを回避するため、`Transcriber` クラスの初期化時に `.venv` 内の `nvidia/cudnn/lib` を `LD_LIBRARY_PATH` へ動的に注入します。

### B. 適応的フォールバック
GPU メモリ不足 (OOM) やドライバ不整合が発生した際、システムは自動的に CPU (`int8`) モードへフォールバックし、パイプラインの停止を防止します。

## 3. 運用上の制約 (Constraints)

- **リソース競合**: 16GB VRAM を搭載していますが、メインアプリケーションと `repair` エージェントを同時に実行すると、Whisper Large v3 などの巨大なモデルのロードにより OOM (Exit 137) が発生する可能性があります。
- **推奨設定**: 並列処理が必要な場合は、`whisper_model_size` を `medium` 以下に下げるか、片方のプロセスを終了させることを推奨します。

---
> [!NOTE]
> この仕様は Protocol v8.0 の Zero-Ops 思想に基づき、環境構築を自動化・抽象化するために作成されました。
