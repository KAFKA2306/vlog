---
codd:
  node_id: "req:overview"
  type: spec
  status: approved
  links:
    - to: docs/SPEC.md
      type: specification
    - to: apps/capture-vrchat/src/vlog_capture/main.py
      type: implementation
    - to: docs/architecture/human-memory-v2.md
      type: architecture
---

# VLog overview

この文書はVLogを短く理解するためのorientationです。製品仕様や現在進捗を重複して保持しません。

- 製品不変条件・保存境界・動作保証: [`SPEC.md`](SPEC.md)
- target architectureとmigration: [`architecture/human-memory-v2.md`](architecture/human-memory-v2.md)
- current executable runtime: [`architecture.md`](architecture.md)
- documentation authority map: [`README.md`](README.md)

## Product direction

```text
Evidence -> Human Memory -> Narrative Artifact -> Public Projection
```

VLogは、VRChat sessionから得たEvidenceをAI生成文で置き換えるのではなく、review可能なmemory claimとprovenanceを保持し、日記・物語・画像などを再生成可能な派生物として扱います。公開はmemory採用とは別のdecisionです。

## Current and target systems

移行中は2つのarchitectureを区別します。

- **Current runtime**: `apps/capture-vrchat/` と `apps/reader/` を中心とする、legacy-compatibleな実行系。
- **Human Memory v2 target**: stable identity、explicit ingestion state、append-only revision、private Evidence storage、canonical persistenceを持つtarget architecture。

「現在動くもの」と「将来の正準構造」を同じstatusとして記述しません。

## Repository scope

- `apps/`: deployable applications
- `packages/`: storage-agnostic domain capabilities
- `adapters/`: persistence、storage、external integrations
- `infra/`: systemd、Windows、Supabase assets
- `schemas/`: versioned interchange contracts
- `docs/`: specifications、architecture、operations、ADRs

private Evidence、personal journal、identity/relationship dataはpublic repositoryのcanonical dataにしません。

## Current status

日付付きのmigration表はこの文書へ置きません。未完了workは[Issue #14](https://github.com/KAFKA2306/vlog/issues/14)、repository stateはcurrent `main` / tests / CI、environment stateは対象environmentの実測で確認します。
