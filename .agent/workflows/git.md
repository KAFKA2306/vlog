# /git — Gitリポジトリ管理プロトコル

本ドキュメントは、Crash-Driven Development (CDD) の哲学に基づき、リポジトリの整合性と透明性を極限まで高めるための Git 操作規定である。

## 1. 核心原則 (Core Principles)

*   **Silent Operator**: コミットメッセージおよび操作において情緒的表現を排除し、事実（ロジックの修正、機能の追加）のみを記述する。
*   **Zero-Fat**: コミットは最小の論理単位（Atomic Commit）で行う。不要なコメントや暫定的な修正を含めない。
*   **Traceability**: 修正コミットは、原因となったスタックトレースまたは論理欠陥（Radical Root Cause）に紐付ける。

## 2. ワークフロー (Workflow)

### Step 0: Purity Gate
コミット前に必ず以下のコマンドを実行し、コードの純粋性を担保する。
```bash
task lint
```
*   `ruff` による自動整形と静的解析を通過すること。
*   警告は無視せず、ロジックの不備として即座に修正する。

### Step 1: Observation
`git status` および `git diff` を使用し、変更範囲が当初の意図（Radical Fix または New Logic）に限定されているか観測する。

### Step 2: Atomic Commit
変更を論理単位ごとにステージングし、コミットする。
```bash
git add <対象ファイル>
git commit -m "<type>: <具体的な内容>"
```

#### Commit Types
*   `feat`: 新機能の論理実装
*   `fix`: 根本原因（Radical Cause）の修正
*   `refactor`: ロジックの純純化（Zero-Fat化）
*   `docs`: 厳密な日本語ドキュメントの更新
*   `chore`: インフラ（Taskfile, systemd）の調整

### Step 3: Verification
プッシュ後、CI/CD またはローカルの `task status` でシステムの整合性を最終確認する。

## 3. インシデント対応 (Incident Response)

*   **Fail Fast**: デプロイ後にクラッシュが発生した場合、それを「情報の獲得」と見なし、スタックトレースを即座に回収する。
*   **Radical Fix Only**: クラッシュを隠蔽する `try-catch` の追加は禁止。上流の論理欠陥を修正するコミットを行う。

## 4. 禁止事項 (Forbidden)

*   `git add .` による無差別なステージング。
*   「修正」「update」といった抽象的で非情報的なコミットメッセージ。
*   コメントアウトされたコードのコミット。
