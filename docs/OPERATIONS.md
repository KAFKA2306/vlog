# VLog operations

Current capture runtimeのdiagnosis、supervision、incident recoveryを扱います。製品保証は[`SPEC.md`](SPEC.md)、target migrationは[`architecture/human-memory-v2.md`](architecture/human-memory-v2.md)が正準です。

## Repository gate

```bash
task verify
```

これはrepository-level verificationです。actual hostのsystemd、Windows Task Scheduler、audio、GPU、Supabase、Vercel、object storage、credentialは対象environmentで別途確認します。

## Supervision

- Linux / WSL: `infra/systemd/`
- Windows host: `infra/windows/`
- runtime diagnosis: `vlog-operations`

Runtime state pathは`vlog_capture.portability.runtime_directories()`が解決します。

### Linux / WSL

```bash
task systemd:verify
task systemd:install
systemctl --user status vlog.service vlog-daily.timer
journalctl --user -u vlog.service -u vlog-daily.service --since "24 hours ago"
```

### Windows

```powershell
powershell.exe -ExecutionPolicy Bypass -File infra/windows/install-vlog-watchdog.ps1
```

Windows verificationはactual Windows hostで行います。

## Diagnose

```bash
uv run --frozen vlog-operations doctor --root "$PWD"
uv run --frozen vlog-operations report --days 30
```

詳細なhost stateが必要な場合だけ`systemctl` / `journalctl`を直接使います。

## Recovery

Incidentは`fingerprint + resource_id`で追跡します。generic success eventはfailureを解決しません。

```bash
uv run --frozen vlog-operations recover-latest \
  --category recording \
  --component audio-recorder \
  --operation start \
  --resource-id audio-input:default \
  --message "Audio input was verified manually"
```

1. raw inputとlogを保持する。
2. failed component/resourceを特定する。
3. canonical boundaryで原因を修正する。
4. focused checkと`task verify`を実行する。
5. affected idempotent operationだけreplayする。
6. output、audit evidence、downstream visibilityを確認する。
7. 未実行のenvironment verificationを明示する。

Structured eventの実装は`apps/capture-vrchat/src/vlog_capture/infrastructure/observability.py`と`apps/capture-vrchat/src/vlog_capture/operations.py`を参照してください。Private path、credential、raw EvidenceをDiscordやPublic Readerへ転記しません。

## Related documents

- [Product specification](SPEC.md)
- [Documentation index](README.md)
- [Maintenance](MAINTENANCE.md)
- [Current runtime architecture](architecture.md)
- [Daily pipeline contract](daily_pipeline_contract.md)
- [Phase 0 inventory](operations/phase0-inventory.md)
