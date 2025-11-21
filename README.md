# VRChat Auto-Diary (vlog)

VRChatのプレイログを自動で記録し、日記としてまとめるツールです。

## 概要

VRChatが起動している間、自動的にマイク音声を録音し、終了後に音声を文字起こしして要約日記を生成します。

## 機能

- **プロセス監視**: VRChatの起動・終了を自動検知
- **自動録音**: プレイ中の音声をバックグラウンドで録音
- **文字起こし**: Faster Whisperを使用した高速・高精度な文字起こし
- **要約生成**: Gemini APIを使用して日記形式に要約
- **Markdown出力**: 日付ごとにMarkdownファイルとして保存

## 必要要件

- Python 3.11以上
- PortAudio (`sudo apt-get install libportaudio2`)
- Google Gemini APIキー

### WSL (Windows Subsystem for Linux) での使用

**プロセス検出**: ✅ Windows上のVRChatを自動検出可能  
**音声録音**: ⚠️ WSLから直接Windowsの音声デバイスにアクセスできないため、音声録音はWindows版での実行が必要

完全な機能を使うにはWindows上で直接実行してください。

### Windowsでの実行（推奨）

**PowerShell（推奨）**:

```powershell
.\run.ps1
```

**コマンドプロンプト**:

```cmd
.\run.bat
```

> **注意**: WSLから直接 `\\wsl$\...` パスでバッチファイルを実行する場合、UNCパスがサポートされていないため、PowerShell版を使用するか、事前にディレクトリに移動してください。

## セットアップ

1. リポジトリをクローン
2. 依存関係をインストール

   ```bash
   uv sync
   ```

3. 設定ファイルの準備

   **APIキーの設定（必須）**:

   ```bash
   cp .env.example .env
   # .envを編集してGOOGLE_API_KEYを設定
   ```

   **アプリケーション設定**:

   基本設定は `config.yaml` で管理されています。GPU（CUDA）を使ったlarge-v3-turboなど、設定を変更したい場合は `config.yaml` を編集してください。

   ```yaml
   # config.yaml の例
   whisper:
     model_size: "large-v3-turbo"  # tiny, base, small, medium, large-v3, large-v3-turbo
     device: "cuda"                # cpu, cuda, auto
     compute_type: "float16"       # int8, float16, float32
     beam_size: 5
     vad_filter: true
   ```

   環境変数でも上書き可能です:

   ```bash
   export VLOG_WHISPER_MODEL_SIZE=large-v3-turbo
   export VLOG_WHISPER_DEVICE=cuda
   export VLOG_WHISPER_COMPUTE_TYPE=float16
   ```

## 設定

### large-v3-turbo（GPU推奨）

VRAM 6GB以上のGPUをお持ちの場合、`large-v3-turbo`の使用を推奨します：

- **性能**: large-v3比で5〜8倍高速、モデルサイズ約1.6GB
- **VRAM**: 約6GB（FP16使用時）、16GBなら余裕あり
- **精度**: baseより大幅に向上

`config.yaml`で以下のように設定してください：

```yaml
whisper:
  model_size: "large-v3-turbo"
  device: "cuda"
  compute_type: "float16"
```

初回実行時にモデル（約1.6GB）をダウンロードします。

### 設定ファイルの優先順位

1. **環境変数** (`VLOG_*`) - 最優先
2. **config.yaml** - デフォルト設定
3. **コードのデフォルト値** - config.yamlがない場合のフォールバック

## 使い方

### systemdサービスとして起動（推奨）

システム起動時に自動的に開始されます。

```bash
# サービスを有効化して起動
systemctl --user enable --now vlog.service

# 状態確認
systemctl --user status vlog

# ログ確認
journalctl --user -u vlog -f
```

### go-taskを使用（開発時）

[go-task](https://taskfile.dev/)をインストールしている場合、以下のコマンドが使用できます。

```bash
# 利用可能なタスク一覧
task --list

# アプリケーション実行
task run

# テスト実行
task test

# コード整形・リント
task format
task lint
task check  # format + lint

# サービス管理
task service:enable   # サービス有効化・起動
task service:status   # 状態確認
task service:logs     # ログ確認
task service:restart  # 再起動
```

### 手動起動

```bash
uv run python -m src.main
```

実行すると常駐し、VRChatの起動を待ち受けます。

## ディレクトリ構成

- `src/`: ソースコード
- `tests/`: テストコード
- `recordings/`: 録音データ（自動生成）
- `diaries/`: 日記データ（自動生成）
