# use_cases

ビジネスロジック層。Domainエンティティを使用し、Infrastructureを調整。

## ファイル

- `process_recording.py` - 録音処理ユースケース

## ProcessRecordingUseCase

録音から要約・保存までの全処理を調整するユースケース。

### 依存

- `Transcriber` - 文字起こし
- `TranscriptPreprocessor` - テキスト前処理
- `Summarizer` - 要約生成
- `SupabaseRepository` - DB保存
- `FileRepository` - ファイル操作

### 処理フロー

1. 音声ファイルから文字起こし
2. トランスクリプトの前処理（フィラー除去、重複削除）
3. 前処理済みテキストから要約生成
4. 要約をSupabaseに保存
5. 処理済み録音をアーカイブに移動

### メソッド

- `execute(audio_path: str)` - ファイルパス指定で処理
- `execute_session(session: RecordingSession)` - セッションオブジェクトで処理

### 呼び出し元

- `app.py` - 自動監視モード（別スレッドで非同期実行）
- `cli.py` - CLI手動実行

## 実装原則

- ユースケースは単一責任
- インフラ層を適切に調整
- ログで進捗を出力
- 失敗したらクラッシュ（エラーハンドリング不要）
