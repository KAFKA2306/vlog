# Cross-platform portability contract

Status: accepted repository architecture; actual-host verification remains separate.

Tracking: #99. Decision record: [ADR-0012](../adr/0012-cross-platform-portability.md).

## Core decision

**physical path is not authority**.

| Concern | Authority |
|---|---|
| code / release identity | Git commit SHA |
| Evidence identity | stable source ID + content hash |
| remote Evidence location | object URI / key |
| environment identity | explicit environment / project / config |
| local absolute path | runtime locator only |

Machine-local pathは1 processからbyte列を見つけるためのlocatorであり、code、Evidence、memory、releaseのdurable identityにはしません。

## Checkout topology

```text
GitHub commit SHA
    ├── Windows-native checkout -> VRChat / physical audio / Task Scheduler
    ├── WSL/Linux-native checkout -> processing / systemd / Linux GPU work
    └── disposable CI checkout
```

WindowsとWSL/Linuxは同じphysical checkoutを共有する必要がありません。Windows-mounted WSL path、WSL UNC、一般UNCはboundary locationであり、canonical production code checkoutではありません。

Evidence transportは別のconcernです。private object-storage cutover完了までは明示的なtemporary data bridgeを許容しますが、それによってcheckout pathをauthorityにはしません。

## Path support matrix

| Path class | Windows production code | WSL/Linux production code | Boundary use |
|---|---|---|---|
| local Windows drive path | supported | foreign | explicit adapter経由でsupported |
| native POSIX path | foreign | supported | explicit adapter経由でsupported |
| WSL Windows-mounted drive path | n/a | not canonical | migration / interoperability only |
| WSL UNC share | not canonical | n/a | migration / interoperability only |
| other UNC | not canonical | foreign | best-effort adapter only |
| spaces / Japanese / Unicode | supported | supported | CI-covered |
| case-only collisions | rejected in Git tree | rejected in Git tree | rejected |
| trailing dot/space / Windows reserved names | rejected in Git tree | rejected in Git tree | rejected |

Long-path supportを設計前提にはせず、checkoutとgenerated pathの深さを抑えます。

## Project-root resolution

Runtime root precedence:

1. validな`VLOG_PROJECT_ROOT`が明示された場合はそれを使う;
2. script/module locationとrepository markerから決定する;
3. invocation cwdはdiagnostic contextにだけ使い、authorityにしない。

PowerShellは`$PSScriptRoot`、batch launcherは`%~dp0`、Pythonはmodule/script locationとrepository markerを使用します。

## Configuration and mutable state

Environment variableはcanonicalなuppercase `VLOG_*` namespaceを使います。secretはGitではなくplatformのsecret/environment storeへ置きます。

Portable target locations:

- Linux config: XDG config home
- Linux state: XDG state home
- Linux cache: XDG cache home
- Windows config: roaming AppData `VLog`
- Windows state / cache: local AppData `VLog`

実際のruntime directory resolutionは`apps/capture-vrchat/src/vlog_capture/portability.py`を正準とします。repo-local source dataのmigration stateを文書へ固定pathとして複製しません。

## Executables and toolchains

Supervised runtimeはinteractive shell profileへ依存しません。実行fileはregistration / rendering前に解決します。

- Windows Scheduled Task: explicit executable、working directory、resolved `uv.exe`.
- systemd: rendered checkout rootとresolved `uv`.
- CI: runner workspaceとtool setup actions.

Python-minor-specific NVIDIA pathを文字列で組み立てず、installed package locationをruntimeで検出します。

## Python packaging

Issue #82 / PR #100でretired `src` package名とruntime `PYTHONPATH`依存は撤去済みです。capture runtimeはuv workspaceのinstallable `vlog_capture` packageとして実行します。

```text
vlog
vlog-service
vlog-daily
vlog-operations
```

Package dependency、Python requirement、console entry pointの正準は`pyproject.toml`と`apps/capture-vrchat/pyproject.toml`です。`python -m src...`やruntime用`PYTHONPATH`を再導入しません。

## Verification boundary

Repository portabilityは継続的に次で検証します。

- Windows-compatible Git filename checker
- `.gitattributes` normalization
- Ubuntu / Windows portability jobs
- PowerShell parser checks
- portability unit tests
- runtime contract checker
- clean relocation / installed-entrypoint checks

これらはphysical-host operationを証明しません。VRChat process detection、physical audio、GPU transcription、Task Scheduler、systemd recovery、live Supabase、full VRChat-to-KafLog flowは対象environmentの実測が必要です。

## Primary references

See [2026 portability references](../references/portability-2026.md).
