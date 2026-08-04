---
description: Human Memory v2境界を維持しながら安全にリファクタリングする手順
---

# VLog Refactor Protocol

## 1. 目的

構造変更によって実行契約、証拠データ、プライバシー境界を壊さない。単純なファイル移動ではなく、import、Taskfile、CI、systemd、Windows、Reader、運用文書を同一の変更単位として扱う。

## 2. 不変条件

- raw evidenceを削除・移動しない。
- root `src/`, `frontend/`, `windows/`, `supabase/`, root systemd unitを復活させない。
- Python runtimeは `apps/capture-vrchat/src/`、Readerは `apps/reader/`、運用資産は `infra/` に置く。
- packagesはappsをimportしない。
- accepted memory claimはprovenanceなしで生成しない。
- Graphiti、Cognee、pgvector、Qdrantを正準データにしない。
- テスト、型、エラー処理、監査ログを削って見かけ上の単純化を行わない。

## 3. 実行手順

1. `git status --short` と対象差分を確認する。
2. `uv run --no-sync python scripts/phase0_inventory.py` が必要なデータ移行か判定する。
3. 依存方向と実行入口を列挙する。
4. 変更後に次を実行する。

```bash
task lint
task test
task doc:check
task systemd:verify
task web:build
```

5. Windows固有変更は `infra/windows/README.md` の検証項目を実機で確認する。
6. Supabase変更はschema、RLS、Storage policy、ページング済みobject inventoryを確認する。
7. 実行していない環境検証を完了扱いにしない。
8. [Git workflow](git.md)に従い、意図したファイルだけをcommitする。

## 4. 完了条件

- CIがgreenである。
- 旧root境界が存在しない。
- portable Markdown link検査が通る。
- runtime import、systemd unit、Windows task、Reader buildの各入口が新パスを参照する。
- rollbackがGit commit単位で可能である。
