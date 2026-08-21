# Current daily pipeline contract

Status: implemented in repository; environment verification required  
Architecture class: legacy-compatible runtime

## Purpose

Daily pipelineは未処理のlocal recordingsを現在のgeneration / synchronization flowへ進めます。Human Memory v2 canonical persistenceへ移行中も、現行behaviorを維持するためのcontractです。

Date-based artifactやexisting-output checkはtarget state modelではありません。stable IDs、explicit ingestion runs、idempotency records、outboxへ置換されるまではlegacy-compatible behaviorとして扱います。

## Execution contract

| Item | Definition |
|---|---|
| Scheduler | `vlog-daily.timer` starts `vlog-daily.service` |
| Timer source | `infra/systemd/vlog-daily.timer.in` |
| Schedule | host local time 09:00。productionはAsia/Tokyoを期待 |
| Missed run | `Persistent=true`によりtimer復帰後のcatch-upを要求 |
| Repository entry point | `task process:daily` |
| Runtime console entry point | `vlog-daily` |
| Preconditions | repository、locked dependencies、runtime directories、必要なaudio/GPU/network/credentialが利用可能 |
| Repository success | commandが0で終了し、該当repository validationが成功 |
| Environment success | actual service runが0で終了し、journalとexpected outputs/downstream stateを実測 |
| Failure | required commandがnon-zeroとなり、failure pathがoperational evidenceを残す |

Timer templateはtimezoneを埋め込みません。対象hostが意図したtimezoneであることをenvironment側で確認します。

## Current processing sequence

1. VRChat state、resource availability、pending local workを確認する。
2. VRChat active中はheavy processingを避ける。
3. eligible recordingをtranscribeする。
4. current pipelineが必要とするmissing narrative / image / evaluation artifactsを生成する。
5. configured projection queueを処理する。
6. selected artifactsをexisting Supabase projectionへsyncする。
7. operational evidenceとnotificationを記録する。

Concrete implementationがこの要約と異なる場合はimplementationを優先します。主要entry pointは[`Taskfile.yaml`](../Taskfile.yaml)、`apps/capture-vrchat/src/vlog_capture/cli.py`、`apps/capture-vrchat/src/vlog_capture/daily.py`です。

## Current data contract

物理directory名はportable runtime resolverとconfigurationに従うため、このcontractでは固定しません。論理的なflowは次です。

| Input | Current output |
|---|---|
| recording Evidence | transcript |
| transcript | summary / structured derived data |
| summaries / derived data | narrative、image、evaluation artifacts |
| selected artifacts | existing Supabase projection |
| runtime operation | structured events、heartbeats、journal、brief notifications |

Existing outputを再利用しmissing artifactだけ生成するbehaviorは、stable identity、complete provenance、concurrent ingestion、transactional outboxの最終保証ではありません。

## Operations

```bash
task systemd:verify
task systemd:install
task status
task logs
task down
```

`task systemd:verify`はrendered unit syntaxを検証します。`task systemd:install`後はactual user manager、timer、journalを別途確認します。

## Completion evidence

Repository evidence:

1. Python / runtime contract checksが成功する。
2. `task test`が成功する。
3. `task doc:check`が成功する。
4. `task systemd:verify`が成功する。

Environment evidence:

1. installed timerのnext triggerとtimezone behaviorを確認する;
2. `journalctl --user -u vlog-daily.service`でactual runとexit statusを確認する;
3. source Evidenceを失わずpending workが進むことを確認する;
4. outputがnon-emptyでcurrent inputへtraceできることを確認する;
5. Supabase syncをlive rows / objects / policy behaviorで確認する;
6. failure notificationとrecovery evidenceをprivate dataを露出せず確認する。

GitHub CIだけではenvironment evidenceを満たしません。

## Replacement criteria

このcontractは、canonical ingestionへ移行してlegacy flowとのreconciliationが完了した後だけretireできます。target criteriaは[`architecture/human-memory-v2.md`](architecture/human-memory-v2.md)を正準とし、ここへphase statusを複製しません。

## Related documents

- [Product specification and guarantees](SPEC.md)
- [Current runtime architecture](architecture.md)
- [Human Memory v2 architecture](architecture/human-memory-v2.md)
- [Operations](OPERATIONS.md)
- [Phase 0 inventory](operations/phase0-inventory.md)
