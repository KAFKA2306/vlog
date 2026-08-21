# VLog Human Memory Engine

[![Test and Security Audit](https://github.com/KAFKA2306/vlog/actions/workflows/test.yml/badge.svg)](https://github.com/KAFKA2306/vlog/actions/workflows/test.yml)
[![Reader Visual Regression](https://github.com/KAFKA2306/vlog/actions/workflows/reader-visual-regression.yml/badge.svg)](https://github.com/KAFKA2306/vlog/actions/workflows/reader-visual-regression.yml)
[![Production Smoke](https://github.com/KAFKA2306/vlog/actions/workflows/production-smoke.yml/badge.svg)](https://github.com/KAFKA2306/vlog/actions/workflows/production-smoke.yml)

VLogは、VRChatで生じた音声、写真、会話、出来事をEvidenceとして扱い、人間が確認できる記憶、日記・物語などの派生物、明示的に承認された公開物へ分離して扱う公開OSSエンジンです。

このREADMEは入口とセットアップだけを担当します。製品仕様と動作保証の正準は[`docs/SPEC.md`](docs/SPEC.md)、文書全体の正準マップは[`docs/README.md`](docs/README.md)です。日付付きの進捗表や一時的なproduction状態はREADMEへ複製しません。

## Core model

```text
Evidence
原音声・写真・動画・全文transcript
        │
        ▼
Human Memory
review可能なepisode・claim・revision
        │
        ▼
Narrative Artifact
日記・物語・画像・振り返り
        │
        ▼
Public Projection
公開を明示承認した成果物だけ
```

- AI生成物はEvidenceや確定済み記憶そのものではありません。
- accepted memory claimはsource Evidenceへのprovenanceを必要とします。
- 訂正は履歴を破壊せずrevisionとして追加します。
- 記憶として採用する判断と公開判断を分離します。
- raw Evidenceはprivateを既定とし、公開repositoryへ保存しません。

詳細な不変条件は[`docs/SPEC.md`](docs/SPEC.md)を参照してください。

## Start here

| 読みたいもの | 正準文書 |
|---|---|
| 製品仕様・動作保証 | [`docs/SPEC.md`](docs/SPEC.md) |
| 文書の責務と優先順位 | [`docs/README.md`](docs/README.md) |
| Human Memory v2 target architecture | [`docs/architecture/human-memory-v2.md`](docs/architecture/human-memory-v2.md) |
| 現行runtime architecture | [`docs/architecture.md`](docs/architecture.md) |
| cross-platform portability | [`docs/architecture/portability.md`](docs/architecture/portability.md) |
| 運用・障害対応 | [`docs/OPERATIONS.md`](docs/OPERATIONS.md) |
| 保守 | [`docs/MAINTENANCE.md`](docs/MAINTENANCE.md) |
| agent向けrouter | [`AGENTS.md`](AGENTS.md) |

Human Memory v2移行の未完了作業は[Issue #14](https://github.com/KAFKA2306/vlog/issues/14)で追跡します。現在状態を判断するときは、`main`の実装・tests・GitHub Actions・対象environmentの実測を優先し、READMEの古いスナップショットで代替しません。

## Repository boundaries

```text
apps/       deployable applications
packages/   storage非依存のdomain capabilities
adapters/   persistence・storage・external integrations
infra/      systemd・Windows・Supabase assets
schemas/    versioned interchange contracts
docs/       specifications・architecture・operations・ADRs
```

capture runtimeは`apps/capture-vrchat/`、Readerは`apps/reader/`にあります。Python runtimeはuv workspace上の`vlog_capture` packageとして提供され、`vlog`、`vlog-service`、`vlog-daily`、`vlog-operations`のconsole entry pointを使用します。

## Setup

必要環境:

- Python `>=3.12,<3.13`
- [`uv`](https://github.com/astral-sh/uv)
- [Task](https://taskfile.dev)
- Readerを扱う場合はBun

```bash
git clone https://github.com/KAFKA2306/vlog.git
cd vlog
uv sync --locked
cp .env.example .env
```

実録音・文字起こし・同期には、対象hostのaudio device、VRChat、GPU/model、network、credentialなどが別途必要です。secretやprivate Evidenceをcommitしません。

## Common commands

```bash
task dev
task test
task doc:check
task systemd:verify
task web:build
```

完全なcommand inventoryと実装は[`Taskfile.yaml`](Taskfile.yaml)を正準とします。READMEへtask一覧を複製しません。

## Verification boundary

VLogでは検証範囲を分けます。

- **repository verified**: tests、schema、boundary、buildなどが対象commitで成功した範囲。
- **CI verified**: GitHub Actionsが対象commitで成功した範囲。
- **environment verified**: 実host、audio、GPU、systemd、Windows Task Scheduler、Supabase、Vercel、object storageなどを実測した範囲。

CI成功だけでenvironment稼働を断定しません。Public Readerを含む保証レイヤーの定義は[`docs/SPEC.md`](docs/SPEC.md)に集約します。

## Privacy boundary

公開repositoryへ保存しないもの:

- 原音声、非公開写真・動画、全文会話・全文transcript
- private journal、個人関係、位置情報などのprivate memory
- API key、token、cookie、credential
- private object storage URLや未公開artifact
- redaction前の運用log

公開物は明示的なpublication decisionを経たprojectionだけとします。
