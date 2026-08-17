# VLog Human Memory Engine

[![Test and Security Audit](https://github.com/KAFKA2306/vlog/actions/workflows/test.yml/badge.svg)](https://github.com/KAFKA2306/vlog/actions/workflows/test.yml)
[![Reader Visual Regression](https://github.com/KAFKA2306/vlog/actions/workflows/reader-visual-regression.yml/badge.svg)](https://github.com/KAFKA2306/vlog/actions/workflows/reader-visual-regression.yml)
[![Companion Pages](https://github.com/KAFKA2306/vlog/actions/workflows/companion-pages.yml/badge.svg)](https://github.com/KAFKA2306/vlog/actions/workflows/companion-pages.yml)

VLogは、VRChatで生じた音声、写真、会話、出来事を証拠として保存し、人間が確認できる記憶、日記、物語、公開物へ段階的に変換するための公開OSSエンジンです。

このリポジトリの目的は、録音から日記を自動生成することだけではありません。**原証拠、人間の記憶、AIが生成した物語、公開物を別の層として扱い、根拠、訂正、非公開境界、公開判断を追跡できるHuman Memory Repository**へ移行しています。

> **現在の大きな移行:** Human Memory Repository v2  
> **進捗の正準:** [Issue #14](https://github.com/KAFKA2306/vlog/issues/14)  
> **公開OSS:** エンジン、schema、移行tool、運用tool、reader  
> **公開しないもの:** 私的な記憶、原音声、写真、会話全文、個人情報  
> **Python:** 3.11以上  
> **主要操作:** `uv` / Task / Bun

---

## Human Memory v2の考え方

```text
Evidence
原音声、写真、会話、全文文字起こし
        │
        ▼
Human Memory
episode、moment、entity、claim、revision
        │
        ▼
Narrative Artifact
日記、小説、イラスト、月次振り返り
        │
        ▼
Public Projection
明示的に公開を承認した成果物だけ
```

日記、小説、イラスト、要約、graph index、vector indexは、原記憶そのものではなく再生成可能なviewです。

`MemoryClaim`をacceptedにするには、source evidenceへの来歴が必要です。AIが文章を生成したという理由だけでは、人間の記憶として確定しません。

訂正では過去値を破壊せず、revisionを追加します。公開は、記憶の採用とは別の判断です。

---

## 現在の状態

| 領域 | 状態 |
|---|---|
| `apps/`、`packages/`、`adapters/`、`infra/`、`schemas/`の境界 | リポジトリへ実装済み |
| Episode、MemoryClaim、MemoryRevision、Artifactなどのdomain model | 実装済み |
| 根拠なしaccepted claimの禁止 | 実装済み |
| SHA-256付きread-only Phase 0 inventory | tool実装済み。production inventoryは未実行 |
| capture runtimeとreaderの新directoryへの移動 | 実装済み |
| portable systemd、Windows、Supabase path | リポジトリへ実装済み。実hostの切替は未検証 |
| private memory repository | 設計済み・未構築 |
| canonical PostgreSQL schema、UUID、idempotency、outbox | 未実装 |
| private object storageへの完全移行 | 未実装 |
| hybrid retrievalとread-first MCP | 未実装 |
| legacy file-stateの撤去 | 移行照合後に実施予定 |

GitHub CIが成功しても、次を証明しません。

- 実hostのsystemd unitが有効化されている
- Windows Task Schedulerが稼働している
- Vercel設定が正しい
- Supabaseの実データとRLSが正しい
- private object storageへ全証拠が移行済み
- GPU文字起こしが動作する

---

## 公開・非公開境界

```text
KAFKA2306/vlog
  公開OSSエンジン、schema、reader、運用・移行tool

private memory repository
  人間が確認した記憶、日記view、訂正、公開policy

private object storage
  原音声、写真、動画、全文証拠

public site
  明示的に承認したprojectionだけ
```

公開リポジトリへ、個人の原音声、会話全文、非公開写真、位置情報、関係者の個人情報を保存しません。

公開する場合も、Evidenceを直接公開するのではなく、公開判断を持つArtifactまたはProjectionを経由します。

---

## リポジトリ構造

```text
vlog/
├── apps/
│   ├── capture-vrchat/   現在のPython録音・処理runtime
│   ├── reader/           現在のNext.js reader
│   ├── api/              将来のHTTP application境界
│   └── mcp/              将来のread-first MCP境界
├── packages/             storageに依存しないdomain capability
├── adapters/             persistence、graph、vector、storage接続
├── infra/
│   ├── supabase/         現在のschemaとmigration
│   ├── systemd/          portable unit templateとinstaller
│   └── windows/          Task Scheduler、bootstrap、watchdog
├── schemas/              version付きinterchange contract
├── docs/                 architecture、ADR、operations
├── tests/                repository-level verification
└── data/                 machine-local evidenceと生成物。原則Git管理外
```

Python import package名は、runtime移行中の互換性維持のため現在も`src`です。`Taskfile.yaml`、CI、systemd template、Windows scriptは`apps/capture-vrchat`をruntime rootとして設定します。

---

## 現行runtime

Human Memory v2のcanonical persistenceを構築している間、現在のruntime動作は維持されています。

- VRChat processの監視
- 音声録音
- 文字起こし
- 日記・物語・画像などの生成
- file existenceとdirectory scanによる処理状態
- Supabase同期
- Next.js reader
- systemdとWindows supervision
- 運用監査と復旧tool

これらのうち、file-based processing stateやdirectory scanはlegacy mechanismです。v2の最終状態では、canonical ingestion stateとoutboxへ移行します。

---

## セットアップ

### 必要環境

- Python 3.11以上
- [`uv`](https://github.com/astral-sh/uv)
- [Task](https://taskfile.dev)
- readerを扱う場合はBun
- 実録音・文字起こしでは対応する音声device、VRChat、モデル、認証情報

### 初期化

```bash
git clone https://github.com/KAFKA2306/vlog.git
cd vlog
uv sync --frozen
cp .env.example .env
```

`.env`へ実値を設定します。APIキー、Supabase key、秘密のstorage情報をcommitしません。

---

## 主なコマンド

### 開発

```bash
task dev
```

### テスト

```bash
task test
```

### Markdown・文書契約

```bash
task doc:check
```

### systemd template検証

```bash
task systemd:verify
```

### reader build

```bash
task web:build
```

### host操作を伴うコマンド

```bash
task up
task status
task sync
task web:deploy
```

これらは、対応するhost、service、credentialが必要です。コマンドが存在することだけで、production運用が有効とは判断しません。

利用可能なtaskと実行内容は`Taskfile.yaml`を確認してください。

---

## 移行前のinventory

legacy evidenceを移動、削除、uploadする前に、非破壊inventoryを作成します。

```bash
uv run --no-sync python scripts/phase0_inventory.py
uv run --no-sync python scripts/check_repository_boundaries.py
```

inventoryは次を記録します。

- file count
- byte size
- SHA-256
- Git tracking状態
- duplicate content
- 現在のcommit

この処理は、証拠を削除、移動、upload、書換えしません。

production inventoryが未実行の状態では、移行対象の総量や重複解消を完了したと主張しません。

---

## canonical rule

### Raw evidence

原音声、写真、動画などのbyte列は、private object storageを最終canonicalとします。

### Metadataとmemory state

PostgreSQL / Supabaseを、次のtarget canonical storeとします。

- source metadata
- episode、moment、entity
- memory claimとrevision
- ingestion state
- outbox event
- publication decision

### 人間が管理する記憶view

private memory repositoryを、次のcanonicalとします。

- review済みjournal text
- policy
- correction
- 人間が維持するmemory view

### 再構築可能なprojection

Graphiti、Cognee、pgvector、Qdrantなどはprojectionです。canonical dataから再生成可能でなければなりません。

### idempotency

目標のingestion idempotency keyは、`source_hash + pipeline_version`です。

---

## readerと公開物

readerの実装は`apps/reader/`にあります。

READMEに記載されていた公開候補URL:

- https://kaflog.vercel.app/

この環境から2026年8月4日に外部応答を確認できなかったため、現在稼働中とは断定しません。Vercelのdeploy、実URL、表示内容、公開データを個別に確認してください。

公開物は、明示的に公開承認されたprojectionだけを含むべきです。

---

## 検証

### repository内で確認できること

- Python test
- schema validation
- accepted claimのprovenance invariant
- repository boundary
- portable path
- systemd template生成
- Windows assetの構造
- reader build
- Markdown governance
- retired documentの再混入防止

### repository外で確認すること

- 録音deviceとVRChat process
- transcription modelのruntime
- systemd enable・restart・failure recovery
- Windows Task Scheduler
- Supabase data、migration、RLS
- private storageのmanifest
- Vercel deploy
- 公開・非公開境界の実運用

検証できない項目は、READMEやCIの記述で代替しません。

---

## 文書

最初に[`docs/README.md`](docs/README.md)を参照してください。

- [`docs/overview.md`](docs/overview.md) — 製品概要と現在状態
- [`docs/architecture/human-memory-v2.md`](docs/architecture/human-memory-v2.md) — target architecture
- [`docs/architecture.md`](docs/architecture.md) — 現行runtime architecture
- [`docs/operations/phase0-inventory.md`](docs/operations/phase0-inventory.md) — inventory runbook
- [`docs/OPERATIONS.md`](docs/OPERATIONS.md) — 運用
- [`docs/MAINTENANCE.md`](docs/MAINTENANCE.md) — 保守
- [`docs/daily_pipeline_contract.md`](docs/daily_pipeline_contract.md) — 現行daily pipeline contract
- [`docs/markdown-governance.md`](docs/markdown-governance.md) — Markdown governance
- [`AGENTS.md`](AGENTS.md) — agent router

genericなagent tutorialや、一時点のservice statusはactive documentationへ混ぜません。

---

## セキュリティとプライバシー

公開リポジトリへ保存しないもの:

- 原音声、写真、動画
- 会話全文
- private journal
- 個人名、関係性、位置情報などの個人情報
- API key、token、cookie、credential
- private object storage URL
- 未公開artifact
- redaction前の運用log

log、screenshot、Issue、PRへ証拠を添付する場合も、公開範囲とredactionを確認します。

---

## 既知の制約

- Human Memory v2は移行中で、canonical PostgreSQL persistenceは未完成です。
- private memory repositoryとprivate object storageの実移行は未完了です。
- 現在も一部の処理状態はfile existenceに依存します。
- graph・vector retrievalは最終構成ではありません。
- systemd、Windows、Supabase、Vercelの実host cutoverは、repository CIだけでは確認できません。
- AI生成の要約や日記は、人間の記憶や事実を自動確定しません。
- 公開承認のない証拠をpublic projectionへ含めてはいけません。

---

## README.mdとAGENTS.md

- `README.md`は、人間が目的、構造、現在状態、使い方、正準、制約を理解する入口です。
- `AGENTS.md`は、AIエージェントを適切なproject-specific instructionへ案内するrouterです。

重要な人間向け情報をAGENTS.mdだけへ置きません。

---

## ライセンス

コードのlicenseはrepositoryの`LICENSE`を確認してください。原証拠、個人の記憶、生成artifact、外部model・serviceには、それぞれ別の権利と利用条件が適用されます。

**README実体監査:** 2026年8月4日
