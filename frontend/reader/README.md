# VRChat Auto-Diary Reader

Next.jsベースのWebリーダー。Supabaseから日記エントリを取得して表示。

## 環境変数

`.env.local`ファイルに以下を設定：

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_...
```

環境変数は親ディレクトリの`.env`から自動抽出可能：

```bash
task web:env  # プロジェクトルートで実行
```

## 開発

### インストール

```bash
cd frontend/reader
npm install
```

### 開発サーバー

```bash
npm run dev -- --hostname 0.0.0.0 --port 3000
# または
task web:dev  # プロジェクトルートから
```

ブラウザで`http://localhost:3000`を開く。

### 本番ビルド

```bash
npm run build
npm run start  # ビルド後のプレビュー
```

## デプロイ

### Vercel（推奨）

```bash
npx vercel --prod
# または
task web:deploy  # プロジェクトルートから
```

プロジェクト名：`kaflog`

### 本番URL

<https://kaflog.vercel.app>

## Supabase設定

### テーブル

`daily_entries`テーブルが必要：

```sql
CREATE TABLE daily_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  file_path TEXT UNIQUE NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
```

### Row Level Security (RLS)

読み取り専用ポリシーを設定：

```sql
ALTER TABLE daily_entries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable read access for all users"
ON daily_entries FOR SELECT
USING (true);
```

## プロジェクト構成

```
frontend/reader/
├── app/              Next.js App Router
│   ├── page.tsx      メインページ
│   └── layout.tsx    レイアウト
├── components/       Reactコンポーネント
├── lib/              ユーティリティ
│   └── supabase.ts   Supabaseクライアント
└── public/           静的ファイル
```

## トラブルシューティング

### Supabase接続エラー

1. `.env.local`の環境変数を確認
2. Supabaseプロジェクトの設定を確認
3. RLSポリシーが有効か確認

### ビルドエラー

```bash
rm -rf .next node_modules
npm install
npm run build
```

