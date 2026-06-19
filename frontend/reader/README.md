# VRChat Auto-Diary Reader

Next.jsベースのWebリーダー。`data/summaries/` のローカルファイルを読み込んで表示。

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

## プロジェクト構成

```
frontend/reader/
├── app/              Next.js App Router
│   ├── page.tsx      メインページ
│   └── layout.tsx    レイアウト
├── lib/              ユーティリティ
│   └── entries.ts    ローカル要約読み込み
└── public/           静的ファイル
```

## トラブルシューティング

### ビルドエラー

```bash
rm -rf .next node_modules
npm install
npm run build
```
