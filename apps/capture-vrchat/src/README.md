# VRChat Capture Runtime

VLog Auto DiaryのPython実行パッケージ。リポジトリ上の配置は `apps/capture-vrchat/src/` だが、挙動維持のためimport名は `src` のまま運用する。

## ディレクトリ構成

- `domain/` - エンティティとインターフェース（外部依存なし）
- `use_cases/` - ビジネスロジック
- `infrastructure/` - 外部依存実装

## アーキテクチャ

```
Entry Points (main.py, app.py, cli.py)
    ↓
Use Cases (process_recording.py)
    ↓
Infrastructure (ai, system, repositories)
    ↓
Domain (entities, interfaces) ← 依存なし
```

## ファイル一覧

| ファイル | クラス/関数 | 責務 |
|----------|------------|------|
| `main.py` | `setup_logging()` | ロギング設定（stdout + file） |
| `app.py` | `Application` | 自動監視メインループ |
| `app.py` | `.run()` | 無限ループ（`check_interval`秒毎） |
| `app.py` | `._tick()` | プロセス監視→録音制御→処理トリガー |
| `cli.py` | `cmd_process()` | `--file`指定で録音処理 |
| `cli.py` | `cmd_novel()` | `--date`指定で小説生成 |
| `cli.py` | `cmd_sync()` | Supabase同期 |
| `cli.py` | `cmd_image_generate()` | 画像生成（`--prompt`または`--novel`） |
| `cli.py` | `cmd_jules()` | Jules AIチャット |
| `cli.py` | `cmd_transcribe()` | 文字起こしのみ |
| `cli.py` | `cmd_summarize()` | 要約生成のみ |
| `cli.py` | `cmd_pending()` | 保留タスク処理 |
| `cli.py` | `cmd_curator()` | コンテンツ評価 |

## 設定パラメータ

| パラメータ | 設定元 | 値 | 説明 |
|-----------|--------|-----|------|
| `check_interval` | config.yaml | 5 | プロセス監視間隔（秒） |
| `process_names` | config.yaml | VRChat.exe,VRChat | 監視対象プロセス名 |

## 実行方法

### 自動監視モード

```bash
python -m src.main
```

### CLI

```bash
python -m src.cli process --file data/recordings/audio.wav
python -m src.cli novel --date 20250120
python -m src.cli sync
```

