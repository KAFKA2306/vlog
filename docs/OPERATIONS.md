# VLog operations

このrunbookはcurrent capture runtimeのdiagnosis、supervision、incident evidence、recoveryを扱います。製品全体の保証レイヤーは[`SPEC.md`](SPEC.md)、target migrationは[`architecture/human-memory-v2.md`](architecture/human-memory-v2.md)を参照してください。

## Verification boundary

Repository validationとenvironment validationは別です。

```bash
task verify
```

このgateはrepository-levelのtest、boundary、systemd template、Reader buildをまとめます。actual hostのsystemd、Windows Task Scheduler、audio、GPU、Supabase、Vercel、object storage、credentialは対象environmentで別途検証します。

## Supervision

- Linux / WSL: `infra/systemd/`
- Windows host: `infra/windows/`
- runtime diagnosis: `vlog-operations`

Runtime state directoryは`vlog_capture.portability.runtime_directories()`が解決します。runbookへmachine-specific absolute pathを固定しません。

## Linux / WSL

```bash
git pull --ff-only
task systemd:verify
task systemd:install
systemctl --user status vlog.service vlog-daily.timer
systemctl --user list-timers vlog-daily.timer --all --no-pager
journalctl --user -u vlog.service -u vlog-daily.service --since "24 hours ago"
```

Template verificationだけではproduction user manager、timer、audio、GPU、credentialの動作を証明しません。

## Windows watchdog

```powershell
powershell.exe -ExecutionPolicy Bypass -File infra/windows/install-vlog-watchdog.ps1
```

Actual Windows hostでscheduled task、WSL/launcher、watchdog recovery、real recording、failure evidenceを確認します。

## Routine diagnosis

```bash
task ops:doctor
task ops:report
```

詳細なLinux host stateが必要な場合だけ`systemctl` / `journalctl`を直接使います。

## Incident identity and recovery

Incidentは`fingerprint + resource_id`で追跡します。generic success eventはfailureを解決しません。Manual verification後は対応するfailureを明示してrecoveryを記録します。

```bash
uv run --frozen vlog-operations recover-latest \
  --category recording \
  --component audio-recorder \
  --operation start \
  --resource-id audio-input:default \
  --message "Audio input was verified manually"
```

該当するopen failureが存在しない場合、commandは成功扱いにしません。

## Recording checks

Actual capture hostでinput stream、non-empty sample flow、recording growth、VRChat session processing、downstream processing、failure/recovery evidenceを確認します。Static testsだけでphysical audio deviceやreal VRChat processを確認したことにはしません。

## Event durability and privacy

Structured eventのformat、rotation、sanitization、durability policyの正準はimplementationです。Current implementationは`apps/capture-vrchat/src/vlog_capture/infrastructure/observability.py`と`apps/capture-vrchat/src/vlog_capture/operations.py`を参照してください。

Detailed log、private path、credential、raw EvidenceをDiscordやpublic Readerへ転記しません。

## Related documents

- [Product specification and guarantees](SPEC.md)
- [Documentation index](README.md)
- [Maintenance procedures](MAINTENANCE.md)
- [Current runtime architecture](architecture.md)
- [Current daily pipeline contract](daily_pipeline_contract.md)
- [Phase 0 inventory](operations/phase0-inventory.md)
