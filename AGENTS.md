# VRChat Auto-Diary - 開発ガイド

## プロジェクト構造

```
src/
├── main.py              メインエントリーポイント
├── app.py               自動監視ループ
├── cli.py               CLIコマンド
├── domain/              RecordingSession
├── infrastructure/      録音、文字起こし、要約、前処理
└── services/            ProcessorService
```

## コマンド

```bash
task setup     依存同期
task dev       開発実行
task lint      コード整形
task clean     キャッシュ削除

task up        systemdサービス起動
task down      systemdサービス停止
task restart   systemdサービス再起動
task status    全体状態確認（systemd + ログ解析）
task logs      ログ追尾

task record                         手動録音
task process FILE=audio.wav         一括処理
task process:all                    全録音を一括処理

task sync                           Supabase同期
task sync:full                      全件強制同期

task web:dev                        フロントエンド開発
task web:deploy                     Vercelデプロイ

# デバッグ用
task service:status                 systemd状態のみ
task log:status                     ログ解析のみ
task transcribe FILE=audio.wav      文字起こしのみ
task summarize FILE=transcript.txt  要約のみ
```

## 設定

- `.env`: GOOGLE_API_KEY
- `config.yaml`: すべての設定値

## コーディング規約

- Python 3.11+、型ヒント必須
- 4スペースインデント、snake_case
- **コメントなし、最小限のコード**
- 設定は config.yaml か .env

## クリーン化の原則

### 削除すべきもの

- 使われていない関数・クラス・変数
- 重複するコード
- 無用なコメント・docstring
- 古い実験用ファイル
- 使われていない設定値
- 空の import

### 保つべきもの

- 実際に使われているコードのみ
- 最小限の設定
- 型ヒント（ドキュメント代わり）
- README.md（各ディレクトリに最小限）

### 実装の指針

- **シンプル第一**: 複雑な抽象化より直接的な実装
- **重複を避ける**: 同じロジックは1箇所に
- **設定を分離**: ハードコードせず config.yaml へ
- **エラーハンドリング不要**: 失敗したらクラッシュさせる
- **リトライ不要**: 1回だけ実行、失敗したら終了
- 要約出力が完了したら `src.sync_supabase.main()` を呼び、`daily_entries` に upsert する（自動監視モードと CLI の summarize/process で共通）
- 再同期やリカバリは `task sync` を手動実行
