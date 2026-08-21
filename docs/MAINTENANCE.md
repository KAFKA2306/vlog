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

Repeatableなrepository / infrastructure maintenanceだけを扱います。point-in-time service statusやmigration進捗はGitHub Issue / PRへ置きます。

## Repository verification

```bash
task verify
```

`Taskfile.yaml`と`.github/workflows/`が実行契約です。Repository checkをproduction host、Windows、Vercel、Supabase、object storage、audio、GPUのverificationとして扱いません。

Environment diagnosisは`vlog-operations`を直接使います。

```bash
uv run --frozen vlog-operations doctor --root "$PWD"
uv run --frozen vlog-operations report --days 30
```

## Documentation

Canonical mapは[`README.md`](README.md)、ownership ruleは[`markdown-governance.md`](markdown-governance.md)です。既存authorityを更新し、parallel specificationを作りません。変更後は`task doc:check`を実行します。

## systemd

```bash
task systemd:verify
task systemd:install
```

Templateは`infra/systemd/`が正準です。Actual user-manager stateとjournalは対象hostで確認します。

## Windows

Canonical assetsは`infra/windows/`です。Task Scheduler、launcher/watchdog recovery、actual recordingはWindows host上で確認します。

## Evidence and storage

Destructive migration前にnon-destructive inventoryを実行します。

```bash
uv run --no-sync python scripts/phase0_inventory.py
```

Retained inventoryとrecoverable backupなしにraw Evidenceを削除・移動しません。migration先とのreconciliation完了前にlegacy Evidenceを削除しません。詳細は[`operations/phase0-inventory.md`](operations/phase0-inventory.md)を正準とします。

## Supabase

Schema、row、RLS、Storage policy変更ではpre-change stateをexportし、`infra/supabase/`のversioned changeを適用してrole別にreconcileします。Connection failureやpartial listingを成功扱いにしません。

## Reader

```bash
task web:dev
task web:build
```

Application rootは`apps/reader/`です。Local buildとproduction release provenanceは別に確認します。

## Recovery order

1. failed componentとsource Evidenceを特定する。
2. logs、manifest、current state、hashを保存する。
3. canonical boundaryでrepairする。
4. focused test後に`task verify`を実行する。
5. affected idempotent operationだけreplayする。
6. outputとdownstream visibilityを確認する。
7. unresolved environment validationを明示する。

## Related documents

- [Documentation index](README.md)
- [Product specification](SPEC.md)
- [Operations](OPERATIONS.md)
- [Current runtime architecture](architecture.md)
- [Human Memory v2](architecture/human-memory-v2.md)
