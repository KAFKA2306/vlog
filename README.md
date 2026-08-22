# VLog Human Memory Engine

[![Test and Security Audit](https://github.com/KAFKA2306/vlog/actions/workflows/test.yml/badge.svg)](https://github.com/KAFKA2306/vlog/actions/workflows/test.yml)
[![Reader Visual Regression](https://github.com/KAFKA2306/vlog/actions/workflows/reader-visual-regression.yml/badge.svg)](https://github.com/KAFKA2306/vlog/actions/workflows/reader-visual-regression.yml)
[![Production Smoke](https://github.com/KAFKA2306/vlog/actions/workflows/production-smoke.yml/badge.svg)](https://github.com/KAFKA2306/vlog/actions/workflows/production-smoke.yml)

VLogは、VRChatのEvidenceからreview可能なHuman Memory、Narrative Artifact、明示承認されたPublic Projectionを生成する公開OSSエンジンです。

このREADMEは入口とセットアップだけを担当します。仕様・保証・運用詳細をここへ複製しません。

## Start here

| 目的 | 正準 |
|---|---|
| 製品仕様・動作保証 | [`docs/SPEC.md`](docs/SPEC.md) |
| 文書マップ | [`docs/README.md`](docs/README.md) |
| Human Memory v2 | [`docs/architecture/human-memory-v2.md`](docs/architecture/human-memory-v2.md) |
| 現行runtime | [`docs/architecture.md`](docs/architecture.md) |
| portability | [`docs/architecture/portability.md`](docs/architecture/portability.md) |
| 運用 | [`docs/OPERATIONS.md`](docs/OPERATIONS.md) |
| 保守 | [`docs/MAINTENANCE.md`](docs/MAINTENANCE.md) |
| agent router | [`AGENTS.md`](AGENTS.md) |

## Repository boundaries

```text
apps/       deployable applications
packages/   storage非依存domain capabilities
adapters/   persistence・storage・external integrations
infra/      systemd・Windows・Supabase assets
schemas/    versioned interchange contracts
docs/       specification・architecture・operations・ADRs
```

Python runtimeはuv workspace上の`vlog_capture` packageです。製品操作は`vlog`、運用診断は`vlog-operations`、repository orchestrationは`task`を使います。

## Setup

必要環境はPython `>=3.12,<3.13`、`uv`、Task、Readerを扱う場合はBunです。

```bash
git clone https://github.com/KAFKA2306/vlog.git
cd vlog
task setup
cp .env.example .env
export VLOG_ENV_FILE="$PWD/.env"
```

`.env.example`のVLog runtime設定は`VLOG_*`が正準です。既存deployment向けの旧環境変数名はruntime互換層だけで受け付けます。systemdではrepository内`.env`を使わず、必要なら`VLOG_ENV_FILE`へ明示的な絶対パスを設定します。

実録音・文字起こし・同期には対象hostのaudio device、VRChat、GPU/model、network、credentialが別途必要です。secretやprivate Evidenceをcommitしません。

## Commands

```bash
uv run --frozen vlog --help
uv run --frozen vlog daily
uv run --frozen vlog-operations --help
task verify
```

`task`はbuild、test、deployment、infrastructure、maintenanceなどrepository作業に限定します。製品CLIのaliasはTaskfileへ重複させません。

## Verification boundary

Repository/CIの成功と、actual host・audio・GPU・systemd・Windows Task Scheduler・Supabase・Vercel・object storageのenvironment verificationは別です。保証レイヤーの定義は[`docs/SPEC.md`](docs/SPEC.md)を正準とします。

Raw Evidence、private memory、credential、redaction前logは公開repositoryへ保存しません。公開物は明示的なpublication decisionを経たprojectionだけです。
