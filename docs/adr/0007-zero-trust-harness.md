---
codd:
  node_id: "req:adr-0007"
  type: adr
  status: accepted
  links:
    - to: apps/capture-vrchat/src/domain/harness.py
      type: implementation
    - to: apps/capture-vrchat/src/infrastructure/harness.py
      type: implementation
    - evidence: "task audit PASS (Confirming TRY/SUCCESS/FAILED/SKIPPED logging and GPU/Disk safety checks)"
    ---


# ADR-0007: ゼロトラスト・ランタイム・ハーネスとインシデント監査システムの導入

## ステータス

承認済み (Accepted)

## コンテキスト

VLogシステムはWhisper（文字起こし）や画像生成などの非常に重いGPU/CPU処理を伴う。
現状、VRChat実行中の競合回避ロジック（ADR-0004）は存在するが、以下の課題がある：

1. **網羅性の不足**: VRChat以外のリソース競合や、ネットワークエラー、API制限などの「インシデント」が構造的に記録・追跡されていない。
2. **監査の欠如**: 処理がスキップされたのか、失敗したのか、成功したのかを事後的に一括検証する仕組みがない。
3. **信頼の過剰**: 処理が完了した（ファイルが生成された）＝正しく出力されたと見なしており、出力内容の整合性検証（ゼロトラスト）が行われていない。

## 意思決定

「ゼロトラスト・ハーネス」を導入し、全タスク実行を厳格に管理・監査する。

### 1. Harness（防護柵）

- タスクを `WEIGHT_LIGHT` と `WEIGHT_HEAVY` に分類する。
- `HEAVY` タスクは実行前に環境条件（VRChat起動状況、GPU VRAM空き状況、ディスク容量等）を厳格にチェックし、条件を満たさない場合は安全にスキップする。

### 2. Incident Auditor（監査人）

- `data/incidents.jsonl` に、あらゆるタスクの「試行」「スキップ」「エラー」「成功」を構造化ログとして記録する。
- 失敗やスキップは「インシデント」として定義し、その理由（VRChat Running, API Timeout等）を明文化する。

### 3. Zero-Trust Verification（整合性検証）

- 各タスク完了直後に、出力された成果物（テキスト、画像、WebP等）の妥当性を機械的に検証する。
- 例：
  - テキスト：ファイルサイズが0でないか、最低限の文字数があるか。
  - 画像：有効な画像ヘッダーを持っているか。
- 検証に失敗した場合は「整合性エラー」としてインシデント記録し、後続のパイプラインに汚染を広げないよう即座に処理を中断（fail-fast）させる。

## 実装計画

1. `apps/capture-vrchat/src/domain/harness.py`: ハーネスのインターフェース、タスクの重み、インシデントのデータモデルを定義。
2. `apps/capture-vrchat/src/infrastructure/harness.py`: 具体的な環境チェックロジック（`GuardDog`）とログ出力（`IncidentLogger`）を実装。
3. `apps/capture-vrchat/src/cli_handlers.py`: 主要CLIコマンド（`process`, `novel`, `sync`, `image-generate`, `jules`, `transcribe`, `summarize`, `pending`, `curator`, `manga`）をハーネスでラップし、実行可否の判断と監査を自動化。
4. `Taskfile.yaml`: `task audit` コマンドを追加し、直近のインシデント履歴を要約表示できるようにする。

## 実装状況

- `apps/capture-vrchat/src/domain/harness.py` と `apps/capture-vrchat/src/infrastructure/harness.py` により、`TRY` / `SUCCESS` / `SKIPPED` / `FAILED` / `VERIFICATION_ERROR` を記録する監査フローを実装済み。
- `apps/capture-vrchat/src/cli_handlers.py` では主要CLIコマンドをハーネス経由で実行している。
- `cmd_notify` と `cmd_check_vrc` は現時点では直接実装のままで、将来的なハーネス接続候補として残っている。
- `task audit` は `PASS / FAIL / UNVERIFIED / NOT_APPLICABLE` の監査判定を返す。

## 影響

- **メリット**:
  - リソース競合によるハードクラッシュをより確実に防止できる。
  - サイレントな失敗（壊れたファイルの生成）を早期発見できる。
  - システムが「なぜ動いていないのか」の診断が容易になる。
- **デメリット**:
  - 実行条件が厳格になるため、一時的なスキップが増える可能性がある。
  - 実行ごとに少量のログ書き込みオーバーヘッドが発生する。
