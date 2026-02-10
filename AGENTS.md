# VRChat Auto-Diary - 開発ガイド

## Global Rules
本プロジェクトは、以下のグローバルなClaude Codeルール（"Silent Operator" フレームワーク）に準拠します。
- [Style Rules](file:///home/kafka/.claude/rules/style.md) - コーディング規約・命名規則
- [System Protocols](file:///home/kafka/.claude/rules/protocols.md) - 終了・委譲・スキル使用プロトコル
- [MCP Context](file:///home/kafka/.claude/rules/mcp-context.md) - 文脈取得・MCP優先順位
> [!NOTE]
> `architecture.md` および `communication.md` は現在グローバルルールに含まれていません。

<line_gap>

Claude Code用のルール・スキル・コマンドは `.claude/` に配置（他プロジェクトにもコピー可能な汎用設定）。

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

read taskfile at first.use task and uv to run something.

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

### Mini Task (Jules)

```bash
task jules:add CONTENT="Buy milk"   # タスク追加 (AI解析)
task jules:list                     # タスク一覧
task jules:done ID=12345678         # タスク完了
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
GOOGLE_JULES_API_KEY=...
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
- Rootへのファイル作成禁止。

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

## MCP (Model Context Protocol)

Model Context Protocol (MCP) を使用して、外部ツールやデータソースと安全に連携します。

### 利用可能なMCPサーバー

1.  **supabase-mcp-server**
    *   **Context**: データベース操作、マイグレーション管理、ログ確認。
    *   **Usage**:
        *   生のSQLを実行するのではなく、可能な限りMCPツール（`run_query`など）を使用してください。
        *   DDL変更（テーブル作成など）は `apply_migration` を使用し、履歴を残します。
        *   データの整合性チェックやアドバイザーツールとしても活用できます。

2.  **netlify**
    *   **Context**: サイトのデプロイ状況確認、環境変数管理。
    *   **Usage**:
        *   `get-deploy` で最新のデプロイステータスを確認。
        *   `manage-env-vars` で本番環境変数を安全に更新。

3.  **WebFetch** (MCP Market)
    *   **Context**: ウェブからの情報収集、最新情報の取得。
    *   **Usage**:
        *   `web_search`: Google検索を実行し、結果の要約を取得します。
        *   `read_url`: 指定したURLのコンテンツをテキストとして取得します。
        *   最新のライブラリ情報やニュースが必要な場合に使用してください。





