# VLog documentation

このdirectoryは、製品仕様、現在runtime、target architecture、運用、decision、historical evidenceを別のauthorityとして管理します。同じ事実や進捗を複数文書へコピーしません。

## Source-of-truth map

| Document | Authority |
|---|---|
| [`SPEC.md`](SPEC.md) | 製品不変条件、保存境界、動作保証、完了判定 |
| [`../README.md`](../README.md) | repository入口、最小setup、主要documentation route |
| [`overview.md`](overview.md) | 非規範的な短いproduct orientation。仕様や進捗の正準ではない |
| [`architecture/human-memory-v2.md`](architecture/human-memory-v2.md) | target architecture、canonical stores、migration phases |
| [`architecture/portability.md`](architecture/portability.md) | cross-platform path/env/filesystem/tool execution contract |
| [`architecture.md`](architecture.md) | current executable runtimeとdeployable boundaries |
| [`OPERATIONS.md`](OPERATIONS.md) | diagnosis、supervision、incident evidence、recovery |
| [`MAINTENANCE.md`](MAINTENANCE.md) | repeatable repository / infrastructure maintenance |
| [`operations/phase0-inventory.md`](operations/phase0-inventory.md) | destructive migration前のnon-destructive inventory |
| [`image.md`](image.md) | current illustration-generation boundary |
| [`adr/README.md`](adr/README.md) | architecture decision index and status |
| [`references/portability-2026.md`](references/portability-2026.md) | portability decisionの一次資料 |
| [`incidents/`](incidents/) | dated historical incident records。current statusではない |
| [`markdown-governance.md`](markdown-governance.md) | Markdown ownership、retention、validation rules |

## Precedence

文書と実装が競合するときは、次の順で判断します。

1. schemas、tests、package manifests、`Taskfile.yaml`、implementation;
2. [`SPEC.md`](SPEC.md) の製品不変条件とverification contract;
3. target architectureと明示的なarchitecture contract;
4. component-specific runbookのcurrent operation;
5. current runtime architectureとpipeline contract;
6. ADRのdecision rationale;
7. historical incidentとarchived observation.

意図した将来状態と現在の実装状態が異なる場合は、両者を分離して記述します。

## Status vocabulary

- **Implemented in repository**: code、schema、tests、templateなどが対象commitに存在する。
- **CI-verified**: 対象commitのrepository checksが成功した。
- **Environment-verified**: 実host、deployment、database、storage、network、GPUなどを実測した。
- **Historical**: 記録された日時・environmentにだけ成立する。
- **Planned**: 採用済み方向性だがproduction implementationを意味しない。

CI成功はenvironment verificationを意味しません。

## Progress and volatile state

READMEやoverviewへ日付付き進捗表、service availability、dependency version、task inventoryをコピーしません。

- 未完了workとacceptance evidence: GitHub Issue / Pull Request
- repository state: current `main`、tests、CI
- live service state: 対象environmentのhealth / deployment / operational evidence
- dated incident: [`incidents/`](incidents/)

## Maintenance rules

- 新しいparallel specificationを作らず、既存authorityを更新する。
- volatile configurationやcommandはmanifest、`Taskfile.yaml`、codeへlinkする。
- repository-relative linksを使い、personal pathを残さない。
- point-in-time observationをnormative runbookへ混ぜない。
- component READMEはそのboundaryとentry pointだけを説明する。
- agent filesはcanonical docsへの短いrouterにする。
- `task doc:check`を実行する。
