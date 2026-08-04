# VRChat Auto-Diary Reader

data/summaries の日次要約を読みやすく表示する Next.js リーダー。

## 依存関係

プロジェクトルートから Bun の固定ロックを同期する。

    task web:setup

依存関係を意図的に更新する場合だけ次を実行し、bun.lock をコミットする。

    task web:lock

## 開発

    task web:dev

ブラウザで http://localhost:3000 を開く。

## 検証

    task web:build

型検査、ESLint、本番ビルドを順番に実行する。

## 本番確認

    task web:start

ブラウザで http://localhost:4000 を開く。

## デプロイ

    task web:deploy

本番 URL は https://kaflog.vercel.app である。
