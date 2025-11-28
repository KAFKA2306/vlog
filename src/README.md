# src

VLog Auto Diaryのメインソースコード。Clean Architectureパターンに従った構造。

## ファイル構成

- `main.py` - メインエントリーポイント（ロギング設定、アプリケーション起動）
- `app.py` - 自動監視ループ（VRChat検出、録音管理、処理トリガー）
- `cli.py` - CLIコマンド実装（process, transcribe, summarize）

## ディレクトリ構成

- `domain/` - エンティティとインターフェース定義（ビジネスロジックの核心）
- `use_cases/` - ビジネスロジック実装（録音処理ユースケース）
- `infrastructure/` - 外部依存実装（録音、文字起こし、要約、DB、ファイル操作）

## アーキテクチャ

```
Entry Points (main.py, app.py, cli.py)
    ↓
Use Cases (process_recording.py)
    ↓
Infrastructure (audio_recorder, transcriber, preprocessor, summarizer, repositories)
    ↓
Domain (entities, interfaces) ← 依存なし
```

## 実行方法

### 自動監視モード

```bash
python -m src.main
```

### CLI

```bash
python -m src.cli process --file data/recordings/audio.wav
```

