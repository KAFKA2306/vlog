# infrastructure

外部依存の実装層。Domain層のインターフェースを実装。

## コア機能

- `audio_recorder.py` - 録音機能（sounddevice、FLAC形式保存）
- `transcriber.py` - 文字起こし（Faster Whisper、日本語特化）
- `preprocessor.py` - トランスクリプト前処理（フィラー除去、重複削除）
- `summarizer.py` - 要約生成（Gemini、日記形式プロンプト）

## データ管理

- `file_repository.py` - ファイル操作（移動、アーカイブ）
- `supabase_repository.py` - Supabase DB操作（upsert、タイムスタンプ管理）

## ユーティリティ

- `process_monitor.py` - プロセス監視（VRChat起動・終了検出）
- `settings.py` - 設定管理（config.yaml、.env読み込み）

## 設定ファイル

- `summarizer_prompt.txt` - Gemini要約プロンプトテンプレート

## 実装原則

- エラーハンドリング不要（失敗したらクラッシュ）
- リトライ不要（1回だけ実行）
- ログは標準ロガーで出力
- 設定はconfig.yamlから取得

