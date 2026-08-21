# VLog operations

このrunbookはcurrent capture runtimeのdiagnosis、supervision、incident evidence、recoveryを扱います。製品全体の保証レイヤーは[`SPEC.md`](SPEC.md)、target migrationは[`architecture/human-memory-v2.md`](architecture/human-memory-v2.md)を参照してください。

## Verification boundary

Repository validationとenvironment validationは別です。

- `task systemd:verify`: rendered user-unit syntaxのrepository-level verification
- `task web:build`: Readerのtypecheck / lint / build
- actual host checks: systemd、Windows Task Scheduler、audio、GPU、Supabase、Vercel、object storage、credential

Operational cutoverを完了扱いする前に、対象environmentの実測evidenceを残します。

## Supervision

- Linux / WSL: `infra/systemd/`
- Windows host: `infra/windows/`
- runtime observability: `vlog-operations` console entry point

Runtime state directoryは`vlog_capture.portability.runtime_directories()`が解決します。runbookへmachine-specific absolute pathを固定しません。

## Linux / WSL install and verification

```bash
git pull --ff-only
task systemd:verify
task systemd:install
systemctl --user status vlog.service vlog-daily.timer
systemctl --user list-timers vlog-daily.timer --all --no-pager
journalctl --user -u vlog.service -u vlog-daily.service --since "24 hours ago"
```

Template renderや`systemd-analyze --user verify`だけでは、production user manager、timer、audio、GPU、credentialの動作を証明しません。

## Windows watchdog

```powershell
powershell.exe -ExecutionPolicy Bypass -File infra/windows/install-vlog-watchdog.ps1
```

Actual Windows hostで次を確認します。

- scheduled taskが存在しenabledである;
- WSL / launcherが意図どおり起動する;
- stale stateをwatchdogが検出し、対象serviceを回復できる;
- real VRChat sessionからnon-empty recordingが生成される;
- logがfailure contextを残し、secretやprivate Evidenceを露出しない。

## Routine diagnosis

```bash
task status
task service:status
task log:status
uv run --frozen vlog-operations doctor --root "$(pwd)"
uv run --frozen vlog-operations report --days 30
```

`task status`はplatform-specific taskを利用します。host layerが存在しない場合は対応するcomponent commandを使います。

## Incident identity and recovery

Incidentは`fingerprint + resource_id`で追跡します。generic success eventはfailureを解決しません。Recoveryは対象failureを明示的に参照するrecovery eventとして記録します。

Manual verification後の例:

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

Actual capture hostで少なくとも次を確認します。

- input stream startup / permission / device selection;
- non-empty sample flowとrecording growth;
- recorder-thread failure / timeout;
- VRChat session processing;
- downstream transcription / generation / sync;
- failure時のstructured evidenceとrecovery。

Static testsだけではphysical audio deviceやreal VRChat processを確認できません。

## Event durability and privacy

Structured eventのformat、rotation、sanitization、durability policyの正準はimplementationです。Current implementationは`apps/capture-vrchat/src/vlog_capture/infrastructure/observability.py`と`apps/capture-vrchat/src/vlog_capture/operations.py`を参照してください。

Detailed log、private path、credential、raw EvidenceをDiscordやpublic Readerへ転記しません。

## Verification gate

Repository changeでは変更boundaryに応じて次を実行します。

```bash
task test
task doc:check
task systemd:verify
task web:build
```

Environment changeでは、さらにaffected systemのactual evidenceが必要です。

## Related documents

- [Product specification and guarantees](SPEC.md)
- [Documentation index](README.md)
- [Maintenance procedures](MAINTENANCE.md)
- [Current runtime architecture](architecture.md)
- [Current daily pipeline contract](daily_pipeline_contract.md)
- [Phase 0 inventory](operations/phase0-inventory.md)
