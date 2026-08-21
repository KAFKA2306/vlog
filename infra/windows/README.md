# Windows 環境ガイド

Windows は VRChat プロセス検知・物理 audio capture・Task Scheduler を担当する。WSL/Linux は Linux-native processing と systemd を担当する。

## 2026 portability contract

- Windows の production checkout は Windows native drive 上に置く。
- WSL/Linux の production checkout は Linux filesystem 上に別 clone を置く。
- `\\wsl$`, `\\wsl.localhost`, 一般 UNC を Windows production checkout の正本にしない。
- `/mnt/c/...` を WSL/Linux production checkout の正本にしない。
- 2つの checkout の同一性は physical path ではなく Git commit SHA で確認する。
- machine-local absolute path は Evidence identity ではない。
- Python runtime は uv workspace の named packages / console entrypoints を使う。
- mutable runtime state は Git checkout ではなく OS 標準の VLog config/data/state/cache home に置く。

正準設計は [`../../docs/architecture/portability.md`](../../docs/architecture/portability.md) を参照する。

## 初回セットアップ

Windows native checkout のプロジェクトルートから実行する。

    bootstrap.bat

リポジトリ直下の `bootstrap.bat` は `infra/windows/bootstrap.bat` を呼び出す。

bootstrap は Python 3.12 の locked uv workspace と GPU extra を同期し、`%APPDATA%\VLog` / `%LOCALAPPDATA%\VLog\Data` / `State` / `Cache` を準備して `VlogAutoDiary` を登録する。repo `.env` や repo-local runtime `data/` は作らない。Task登録時に `cmd.exe` と `uv.exe` の実体を解決し、Actionの `WorkingDirectory` を現在のWindows native checkoutへ固定する。

secret/configをdotenvから供給する必要がある場合は、repo外のabsolute fileを用意して `VLOG_ENV_FILE` として明示する。

## 手動起動

    run.bat

`run.bat` は `%~dp0` からproject rootを解決する。UNC/WSL share上のcode checkoutはfail-fastする。Task Schedulerから渡されたabsolute `VLOG_UV_EXE` を優先し、interactive PATH/profileに依存しない。アプリ起動はinstalled `vlog-service` entrypointを使う。

CUDA/cuDNN/cuBLASのWindows DLL directoryは `.venv-win` のPython minor versionを文字列で組み立てず、installed `nvidia` packageからruntime discoveryする。

## 状態確認

    schtasks /Query /TN VlogAutoDiary /V /FO LIST
    uv run --frozen python scripts/vlog_doctor.py

確認する項目:

- Task Action executableがabsolute `cmd.exe` である。
- Task WorkingDirectoryが現在のWindows native checkoutである。
- `uv.exe` のresolved pathがregistration時と一致する。
- runtime data/stateがcheckout外に解決されている。
- VRChat起動後に実録音transitionが発生する。
- commit SHA・Windows version・実行日時を実機E2E Issue #70へ記録する。

repository CIやPowerShell parser PASSは、Task Scheduler・VRChat・audio deviceの実機動作保証を代替しない。

## ログ

標準値では次を参照する。

    Get-Content "$env:LOCALAPPDATA\VLog\State\logs\windows-bootstrap.log" -Tail 50
    Get-Content "$env:LOCALAPPDATA\VLog\State\logs\vlog.log" -Tail 50

`VLOG_STATE_HOME` を設定した場合はその配下の `logs/` がauthorityになる。

## 停止と再起動

    schtasks /End /TN VlogAutoDiary
    schtasks /Run /TN VlogAutoDiary

## トラブルシューティング

### checkoutがUNC/WSL shareにある

code checkoutをlocal Windows driveへcloneし直す。path mappingや`pushd`による一時drive化をproductionの正解にしない。

### Taskではuvが見つからない

`register_task.ps1` を再実行し、registration時に解決された `uv.exe` を確認する。PowerShell profile aliasやinteractive shellだけのPATHをTaskの前提にしない。

### 依存関係が再現できない

    set UV_PROJECT_ENVIRONMENT=.venv-win
    set UV_LINK_MODE=copy
    set UV_PYTHON=3.12
    uv sync --locked --extra gpu

Python support contractは3.12系、package authorityはroot uv workspaceと`uv.lock`である。
