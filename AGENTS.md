# VRChat Auto-Diary - 開発ガイド

変更後は、必ず `task lint` でコード品質をチェックし、`task dev` または `task process FILE=...` で動作確認する。

## プロジェクト構造

```
src/
├── main.py                     メインエントリーポイント（ロギング設定）
├── app.py                      自動監視ループ（VRChat検出、録音管理）
├── cli.py                      CLIコマンド実装
├── domain/
│   ├── entities.py             RecordingSessionエンティティ
│   └── interfaces.py           インターフェース定義
├── infrastructure/
│   ├── audio_recorder.py       録音機能
│   ├── transcriber.py          文字起こし（Faster Whisper）
│   ├── preprocessor.py         トランスクリプト前処理
│   ├── summarizer.py           要約（Gemini）
│   ├── supabase_repository.py  Supabase DB操作
│   ├── file_repository.py      ファイル操作
│   ├── process_monitor.py      プロセス監視
│   └── settings.py             設定管理
└── use_cases/
    └── process_recording.py    録音処理ユースケース
```

## アーキテクチャ原則

- **Clean Architecture**: Domain → Use Cases → Infrastructure の依存方向
- **Dependency Inversion**: インターフェースを通じた依存
- **Minimal Code**: コメント、docstring、エラーハンドリング不要
- **Configuration Separation**: ハードコード禁止、config.yamlで管理

## コマンド一覧

### セットアップ・開発

```bash
task setup     # 依存同期（uv sync）
task dev       # 開発実行（自動監視モード）
task lint      # コード整形・品質チェック（ruff）
task clean     # キャッシュ削除
```

### サービス管理（systemd）

```bash
task up        # systemdサービス起動
task down      # systemdサービス停止
task restart   # systemdサービス再起動
task status    # 全体状態確認（systemd + ログ解析）
task logs      # ログ追尾（リアルタイム）
```

### 録音・処理

```bash
task process FILE=audio.wav         # 1ファイル処理（全工程）
task process:all                    # 全録音を一括処理
task process:today                  # 今日の録音を一括処理（要約再生成）
```

### データ同期

```bash
task sync                           # Supabase同期（差分のみ）
task sync:full                      # 全件強制同期
```

### フロントエンド

```bash
task web:dev                        # 開発サーバー起動
task web:build                      # 本番ビルド
task web:deploy                     # Vercelデプロイ
task web:env                        # 環境変数抽出
```

### デバッグ用

```bash
task service:status                 # systemd状態のみ
task log:status                     # ログ解析のみ
task transcribe FILE=audio.wav      # 文字起こしのみ
task transcribe:all                 # 全録音を文字起こしのみ
task summarize FILE=transcript.txt  # 要約のみ
```

### Git操作

```bash
task commit MESSAGE="commit message"  # git add . && git commit
```

## 起動方法

### Windows

- `windows\run.bat` をダブルクリック
- 初回セットアップ（管理者権限）: `windows\bootstrap.bat`

### Linux/WSL

```bash
task dev     # 開発実行
task up      # systemdサービス起動
```

## 設定ファイル

### `.env`

```bash
GOOGLE_API_KEY=...
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

### `config.yaml`

すべてのシステムパラメータを管理：

- `process`: 監視対象プロセス名、チェック間隔
- `paths`: ディレクトリパス（recordings, transcripts, summaries, archives）
- `audio`: サンプルレート、チャンネル数、無音閾値
- `processing`: 最小ファイルサイズ、処理済みスキップ、アーカイブ設定
- `whisper`: モデル、デバイス、VAD設定、言語
- `gemini`: モデル名

## コーディング規約

- Python 3.11+、型ヒント必須
- 4スペースインデント、snake_case（関数・モジュール）、PascalCase（クラス）
- **コメント禁止、docstring禁止**
- **エラーハンドリング禁止**: 失敗したらクラッシュさせる
- **リトライ禁止**: 1回だけ実行
- 設定は `config.yaml` または `.env` に分離

## クリーン化の原則

### 削除すべきもの

- 使われていない関数・クラス・変数
- 重複するコード
- 無用なコメント・docstring
- 古い実験用ファイル
- 使われていない設定値
- 空のimport
- try-exceptブロック
- リトライ・タイムアウトロジック

### 保つべきもの

- 実際に使われているコードのみ
- 最小限の設定
- 型ヒント（ドキュメント代わり）
- README.md（各ディレクトリに最小限）

## 実装の指針

### データフロー

1. VRChat起動検出（`ProcessMonitor`）
2. 録音開始（`AudioRecorder`）
3. VRChat終了検出
4. 録音停止 → `RecordingSession` 生成
5. `ProcessRecordingUseCase.execute_session()` を別スレッドで実行
   - 文字起こし（`Transcriber`）
   - 前処理（`TranscriptPreprocessor`）
   - 要約（`Summarizer`）
   - Supabase同期（`SupabaseRepository`）
   - ファイル移動（`FileRepository`）

### 同期ポイント

- `ProcessRecordingUseCase` 内で要約完了後、自動的に `SupabaseRepository.upsert()` を呼ぶ
- CLI `task process` も同じユースケースを使用
- 自動監視モード（`app.py`）も同じユースケースを使用
- 再同期やリカバリは `task sync` を手動実行

### 依存の方向

```
Domain (entities, interfaces)
    ↑
Use Cases (process_recording)
    ↑
Infrastructure (audio_recorder, transcriber, summarizer, repositories)
    ↑
Entry Points (main.py, app.py, cli.py)
```

### テスト戦略

- 本番データで動作確認（`task process FILE=...`）
- 失敗したらログで確認（`logs/vlog.log`）
- ユニットテストなし（シンプル第一）

## トラブルシューティング

### ログ確認

```bash
task status       # systemd状態 + ログ解析
task logs         # リアルタイムログ
cat logs/vlog.log # ログファイル直接閲覧
```

### よくある問題

1. **VRChatが検出されない**: `config.yaml` の `process.names` を確認
2. **文字起こしが遅い**: `config.yaml` の `whisper.model_size` を `medium` に変更
3. **要約が失敗**: `.env` の `GOOGLE_API_KEY` を確認
4. **Supabase同期失敗**: `.env` の認証情報とテーブル定義を確認
