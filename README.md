# VRChat Auto-Diary

VRChatプレイ中の音声を自動録音し、文字起こし後に日記形式で要約するツール。

## セットアップ

```bash
uv sync
cp .env.example .env
# .envにGOOGLE_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEYを設定
```

## 使い方

### 自動監視モード

```bash
task up      # サービス起動
task status  # 状態確認
task logs    # ログ確認
task down    # サービス停止
```

### 手動処理

```bash
task record                         # 録音
task transcribe FILE=audio.wav      # 文字起こし
task summarize FILE=transcript.txt  # 要約
task process FILE=audio.wav         # 一括処理

task sync                           # summaries/*.txt を Supabase にupsert
```

## 設定

- `.env`: APIキー (GOOGLE_API_KEY)
- `.env`: APIキー (GOOGLE_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
- `config.yaml`: プロセス監視、音声、Whisper、Gemini設定

## 構成

```
recordings/   音声ファイル
transcripts/  生トランスクリプト
summaries/    日記形式要約
src/          ソースコード
```

## Supabase同期

1. Supabaseの `daily_entries` テーブルを用意（`file_path` を unique）。
2. `.env` に `SUPABASE_URL` と `SUPABASE_SERVICE_ROLE_KEY` を設定。
3. `task sync` で `summaries/*.txt` を `daily_entries` にupsert。

## フロントエンド（reader）

- ローカル: `cd frontend/reader && npm run dev -- --hostname 0.0.0.0 --port 3000`
- 本番URL: https://kaflog-otovlmp1s-kafka2306s-projects.vercel.app
- デプロイ: `cd frontend/reader && npx vercel --prod`（Vercelプロジェクト名 `kaflog`）
