# Windows 環境ガイド

Windows は VRChat プロセス検知・物理 audio capture・Task Scheduler を担当する。WSL/Linux は Linux-native processing と systemd を担当する。

## 2026 portability contract

- Windows の production checkout は Windows native drive 上に置く。
- WSL/Linux の production checkout は Linux filesystem 上に別 clone を置く。
- `\\wsl$`, `\\wsl.localhost`, 一般 UNC を Windows production checkout の正本にしない。
- `/mnt/c/...` を WSL/Linux production checkout の正本にしない。
- 2つの checkout の同一性は physical path ではなく Git commit SHA で確認する。
- machine-local absolute path は Evidence identity ではない。
- Evidence transport の object-storage cutover (#73) が完了するまで、legacy `data/` bridge は明示的な互換境界として扱う。shared **code checkout** に戻してはいけない。

正準設計は [`../../docs/architecture/portability.md`](../../docs/architecture/portability.md) を参照する。

## 初回セットアップ

Windows native checkout のプロジェクトルートから実行する。

    bootstrap.bat

リポジトリ直下の `bootstrap.bat` は `infra/windows/bootstrap.bat` を呼び出す。

bootstrap は `.env`、legacy data directories、`.venv-win` を準備し、`VlogAutoDiary` を登録する。Task登録時に `cmd.exe` と `uv.exe` の実体を解決し、Actionの `WorkingDirectory` を現在のWindows native checkoutへ固定する。

## 手動起動

    run.bat

`run.bat` は `%~dp0` からproject rootを解決する。UNC/WSL share上のcode checkoutはfail-fastする。Task Schedulerから渡されたabsolute `VLOG_UV_EXE` を優先し、interactive PATH/profileに依存しない。

現在のPython application packageはmigration互換のため `src` のままであり、`PYTHONPATH` も残る。これは #82 のuv workspace移行までのlegacy compatibilityであり、正準設計ではない。

CUDA/cuDNN/cuBLASのWindows DLL directoryは `.venv-win` のPython minor versionを文字列で組み立てず、installed `nvidia` packageからruntime discoveryする。

## 状態確認

    schtasks /Query /TN VlogAutoDiary /V /FO LIST
    python scripts/vlog_doctor.py

確認する項目:

- Task Action executableがabsolute `cmd.exe` である。
- Task WorkingDirectoryが現在のWindows native checkoutである。
- `uv.exe` のresolved pathがregistration時と一致する。
- VRChat起動後に実録音transitionが発生する。
- commit SHA・Windows version・実行日時を実機E2E Issue #70へ記録する。

repository CIやPowerShell parser PASSは、Task Scheduler・VRChat・audio deviceの実機動作保証を代替しない。

## ログ

    Get-Content data/logs/windows-bootstrap.log -Tail 50
    Get-Content data/logs/vlog.log -Tail 50

legacy runtimeではログがrepo-local `data/` に残る。config/state/cacheをOS標準directoryへ分離する移行は #84 で追跡する。

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
    uv sync --frozen

Python support contract自体は #95、package/workspace移行は #82 で追跡する。
