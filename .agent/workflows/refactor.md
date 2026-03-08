---
description: 複雑性の最小化と品質維持のための統合プロトコル
---

# VLog Refactor Protocol (Compact Edition)

// turbo-all

> [!IMPORTANT]
> **鉄の掟**: 本文書はプロジェクトの最高位プロトコルである。例外なき遵守を要求する。

## 1. 目的と完了基準
極限の単純化による保守性の最大化を目的とする。以下の基準を満たさないコードはマージ不可。

| 項目 | 基準 |
| :--- | :--- |
| **Comments** | `//`, `#` 等のコメントを一切排除（コードで語る）。 |
| **Error Handling** | `Result` は全て `.unwrap()`。想定外は即座に Panic させる。 |
| **Tests** | `tests/` や単体テストを全削除。実機動作のみで検証。 |
| **Typing** | 型推論を避け、全ての型を明示的に定義する。 |
| **Architecture** | Interface -> UseCase -> Domain <- Infrastructure の依存方向を厳守。 |
| **Files** | 200行超のファイル、および役割不明/重複ファイルの徹底排除。 |

---

## 2. 環境とサービス監査
### 2.1 Rust & System
- **Rust Audit**: `just check` (Clippy/Check), `cargo check --locked`
- **Services**: `task service:status` (vlog.service/timer), `task status` (App status)
- **Logs**: `journalctl --user -u vlog -n 100` で Panic/Error がないか確認。

### 2.2 Secrets & Sync
- **Secrets**: `.env` の各キーが有効な形式か確認。`task web:env` で同期。
- **Sync**: `task sync` 実行後、ローカルと DB の行数が一致することを確認。

---

## 3. データとコンテンツの整合性
- **物理監査**: `recordings/` (60s+) に対し必ず `summaries/` が存在すること。
- **物語品質**: 小説は500文字以上。評価スコア 0.8 未満は再生成。
- **掃除**: `task clean` または `just clean` を実行後、0バイトファイル、60分以上放置された `.tmp`、許可リスト外のディレクトリを `rm -rf` で削除。

---

## 4. アーキテクチャとロジック
- **DIP**: Domain 層が Infrastructure 層を import することを禁止。
- **型指向**: 不正な状態を表現不可能にする（`Enum` や NewType `struct` の活用）。
- **統廃合**: 似たロジックは即座に統合。新機能追加より先に既存コードの削減を検討。
- **単純性**: 常に最も素朴な実装を選択。高度な機能や難解なアルゴリズムを避ける。

---

## 5. 運用コマンド一覧

| カテゴリ | コマンド例 | 用途 |
| :--- | :--- | :--- |
| **Audit** | `just check` / `task lint` | 高精度・高速なコード品質検証。 |
| **Operate** | `task process:daily` | 日次パイプライン（要約・小説・評価）を一括。 |
| **Sync** | `task sync` | Supabase への最終データ同期（必須）。 |
| **Repair** | `task clean` / `just clean` | キャッシュ削除、ゴミ出し、環境リセット。 |
| **Web** | `task web:dev` / `build` | フロントエンド開発とビルド確認。 |

## 7. 視覚的プロトコル

### 7.1 リファクタリング・ループ (Workflow)
```mermaid
graph TD
    Start([Refactor Start]) --> Audit[2. Environment & Service Audit]
    Audit --> Check{Pass?}
    Check -- No --> Repair[5. Repair / Clean]
    Repair --> Audit
    Check -- Yes --> Logic[4. Architecture & Logic Refactor]
    Logic --> Integrity[3. Data Integrity Check]
    Integrity --> FinalCheck{Met 1. Criteria?}
    FinalCheck -- No --> Logic
    FinalCheck -- Yes --> Git[6. Git Push]
    Git --> End([Refactor Complete])
```

### 7.2 エージェント実行フロー (Sequence)
```mermaid
sequenceDiagram
    participant A as Antigravity (Agent)
    participant C as Codebase (Rust/Web)
    participant S as System (task/just/db)
    participant G as Git (Repository)

    A->>S: just check / task lint
    S-->>A: Status/Diagnostic
    A->>C: Apply Iron Rules (Refactor)
    A->>S: task clean / sync
    S-->>A: Consistency Confirmation
    A->>S: task process:daily (Validation)
    S-->>A: Performance/Quality Results
    A->>G: /git (Commit & Push)
    G-->>A: Remote Updated
```

---
*Created by Antigravity for Project VLOG. Simplicity is the ultimate sophistication.*

## 6. 完了後の手順
本プロトコルの完了後、必ず `[git.md](file:///home/kafka/vlog/.agent/workflows/git.md)` ( `/git` ) を呼び出し、変更をコミット・プッシュすること。
