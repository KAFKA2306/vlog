---
codd:
  node_id: "req:maintenance"
  type: spec
  status: approved
  links:
    - to: Taskfile.yaml
      type: implementation
---

# VLog maintenance manual

この文書はrepeatableなrepository / infrastructure maintenanceだけを扱います。point-in-time service statusやmigration進捗はここへ固定しません。

## Routine repository verification

```bash
task verify
```

`Taskfile.yaml`と`.github/workflows/`を実行契約とします。repository checkをproduction host、Windows、Vercel、Supabase、object storage、audio、GPUのverificationとして報告しません。

Environment diagnosis:

```bash
task ops:doctor
task ops:report
```

## Documentation maintenance

Canonical mapは[`README.md`](README.md)、ownership ruleは[`markdown-governance.md`](markdown-governance.md)です。変更時はauthorityを1か所だけ更新します。

1. executable behavior / schema / commandを先に変更する;
2. product invariantやverification contractなら[`SPEC.md`](SPEC.md)を更新する;
3. target architecture / migration designなら[`architecture/human-memory-v2.md`](architecture/human-memory-v2.md)を更新する;
4. current runtime structureなら[`architecture.md`](architecture.md)、operationなら[`OPERATIONS.md`](OPERATIONS.md)を更新する;
5. root README / `overview.md`は入口やrouteが変わる場合だけ更新し、status tableを複製しない;
6. dated incidentは`incidents/`、unfinished work / acceptance evidenceはGitHub Issue / PRへ置く;
7. `task doc:check`を実行する。

Dependency version、Python requirement、console entry point、task inventoryはmanifest / `Taskfile.yaml`へlinkし、Markdownへコピーしません。

## systemd

```bash
task systemd:verify
task systemd:install
```

Templateは`infra/systemd/`を正準とします。Failure時はsource template、rendered unit、user-manager state、journal、runtime evidenceを保存してからrepairします。missing user busはenvironment blockerです。

## Windows

Canonical assetsは`infra/windows/`です。Task Scheduler registration、WSL startup、launcher/watchdog recovery、actual recordingをWindows host上で確認します。WSL-only executionをWindows verificationとは扱いません。

## Evidence and storage

Destructive migration前にnon-destructive inventoryを実行します。

```bash
uv run --no-sync python scripts/phase0_inventory.py
```

retained inventoryとrecoverable backupなしにraw Evidenceを削除・移動しません。remote listingはpagination exhaustionまで取得し、source identity、hash、byte total、object key、visibilityをreconcileします。migration先とのreconciliation完了前にlegacy Evidenceを削除しません。

手順は[`operations/phase0-inventory.md`](operations/phase0-inventory.md)を正準とします。

## Supabase changes

Schema、row、RLS、Storage policyを変更するときはpre-change stateをexportし、versioned changeを`infra/supabase/`から適用し、role別にreconcileします。Connection failure、partial listing、missing credentialをsuccessful migrationとして扱いません。

## Reader

```bash
task web:dev
task web:build
```

Application rootは`apps/reader/`です。Local buildとproduction deploy / release provenanceは別に確認します。

## Human Memory v2 phase changes

Phaseを進める前にrepository-only acceptanceとenvironment acceptanceを分離し、private inventory / export / reconciliation artifactをpublic Gitへ置きません。replacementをreconcileするまでlegacy Evidenceを保持し、raw-data movementと無関係なstructural refactorを同一operationにしません。

## Recovery order

1. failed componentとsource Evidenceを特定する;
2. logs、manifest、current state、hashを保存する;
3. canonical boundaryでconfiguration / codeをrepairする;
4. focused testの後に`task verify`を実行する;
5. affected idempotent operationだけreplayする;
6. output、operational evidence、downstream visibilityを確認する;
7. sourceとrepaired stateをreconcileする;
8. unresolved environment validationを明示する。

## Related documents

- [Documentation index](README.md)
- [Product specification and guarantees](SPEC.md)
- [Operations](OPERATIONS.md)
- [Current runtime architecture](architecture.md)
- [Human Memory v2 architecture](architecture/human-memory-v2.md)
- [Current daily pipeline contract](daily_pipeline_contract.md)
