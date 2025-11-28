# VRChat Auto-Diary

VRChatプレイ中の音声を自動録音し、文字起こし後に日記形式で要約するツール。

## 特徴

- VRChat起動・終了の自動検出
- バックグラウンド録音（FLAC形式）
- Faster Whisperによる高速文字起こし
- Geminiによる日記形式要約
- Supabaseへの自動同期
- Next.jsベースのWebリーダー

## セットアップ

```bash
uv sync
cp .env.example .env
# .envに以下を設定:
#   GOOGLE_API_KEY
#   SUPABASE_URL
#   SUPABASE_SERVICE_ROLE_KEY
#   NEXT_PUBLIC_SUPABASE_URL
#   NEXT_PUBLIC_SUPABASE_ANON_KEY
```

### Windowsでの実行

ダブルクリック、またはコマンドプロンプトから：

```cmd
windows\run.bat
```

初回セットアップ（自動起動登録、管理者権限で実行）：

```cmd
windows\bootstrap.bat
```

`bootstrap.bat`は`.env`を生成し、必要なディレクトリを作成します。

### Linux/WSLでの実行

```bash
task dev     # 開発実行
task up      # systemdサービス起動（自動監視）
```

## 使い方

### 自動監視モード

```bash
task up      # サービス起動（VRChat起動・終了を監視）
task status  # 全体状態確認（systemd + ログ解析）
task logs    # ログ追尾（リアルタイム）
task down    # サービス停止
```

### 手動処理

```bash
task process FILE=audio.wav         # 1ファイル処理（文字起こし→前処理→要約→同期）
task process:all                    # 全録音を一括処理
task process:today                  # 今日の録音を一括処理

task transcribe FILE=audio.wav      # 文字起こしのみ
task summarize FILE=transcript.txt  # 要約のみ
task sync                           # Supabase同期のみ
```

## 設定

- `.env`: API Key、Supabase認証情報
- `config.yaml`: 全システム設定（監視間隔、音声設定、Whisper/Geminiパラメータ）

## 構成

```text
vlog/
├── data/
│   ├── recordings/    録音ファイル（FLAC）
│   ├── transcripts/   文字起こし結果（TXT）
│   ├── summaries/     日記形式要約（TXT）
│   └── archives/      処理済み録音の移動先
├── logs/              システムログ
├── src/
│   ├── main.py              エントリーポイント
│   ├── app.py               自動監視ループ
│   ├── cli.py               CLI実装
│   ├── domain/              エンティティとインターフェース
│   ├── infrastructure/      録音、文字起こし、要約、DB処理
│   └── use_cases/           ビジネスロジック
├── windows/           Windows実行スクリプト
├── frontend/reader/   Next.jsベースのWebリーダー
├── Taskfile.yaml      タスクランナー定義
└── config.yaml        システム設定
```

## データフロー

1. VRChat起動検出 → 録音開始
2. VRChat終了検出 → 録音停止
3. 音声ファイル → Faster Whisper → テキスト
4. テキスト → 前処理（フィラー除去、重複削除）
5. 前処理済みテキスト → Gemini → 日記形式要約
6. 要約 → Supabase `daily_entries` テーブルに自動保存
7. 処理済み録音 → `data/archives/`に移動

## Supabase同期

### テーブル定義

```sql
CREATE TABLE daily_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  file_path TEXT UNIQUE NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
```

### 同期コマンド

```bash
task sync       # data/summaries/*.txt を自動同期
task sync:full  # 全件強制同期（タイムスタンプ更新）
```

## フロントエンド（reader）

### 開発

```bash
task web:dev      # 開発サーバー起動（localhost:3000）
task web:build    # 本番ビルド
```

### デプロイ

```bash
task web:deploy   # Vercelに本番デプロイ
```

### 本番URL

<https://kaflog.vercel.app>

## トラブルシューティング

### 状態確認

```bash
task status       # systemd状態 + ログ解析
task logs         # リアルタイムログ
```

### ログファイル

`logs/vlog.log` にすべての動作記録が残ります。

## 開発

詳細は[AGENTS.md](AGENTS.md)を参照。

```bash
task lint         # コード品質チェック
task clean        # キャッシュ削除
```
