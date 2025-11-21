# インフラストラクチャ層 (src/infrastructure)

外部システムやライブラリとの具体的な連携実装を担当します。

## コンポーネント
- `audio_recorder.py`: マイク入力の録音 (SoundDevice, SoundFile)
- `transcriber.py`: 音声の文字起こし (Faster Whisper)。CUDA失敗時のCPU/
  baseフォールバックと、無音・例外時も必ず文字列を返す安全設計を実装。
- `summarizer.py`: テキスト要約 (Google Gemini API)
- `diary_writer.py`: ファイル出力
- `process_monitor.py`: プロセス監視 (psutil)
- `settings.py`: 設定管理・環境変数読み込み
