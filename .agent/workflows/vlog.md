---
description: VLogの診断、実行、復旧、データ完全性確認を行う統合手順
---

# /vlog — VLog Operations Protocol

## 1. 現行構成

- Python runtime: `apps/capture-vrchat/src/`（import package名は `src`）
- Next.js Reader: `apps/reader/`
- systemd templates: `infra/systemd/*.in`
- Windows bootstrap/watchdog: `infra/windows/`
- Supabase schema/migrations: `infra/supabase/`
- machine-local evidence/artifacts: `data/`

`Taskfile.yaml` が共通入口であり、`PYTHONPATH` を新しいアプリ境界へ設定する。

## 2. 診断

```bash
task status
task service:status
task log:status
uv run python -m src.operations doctor --root "$(pwd)"
uv run python -m src.operations report --days 30
```

診断はログ、プロセス、heartbeat、出力ファイルを相互照合する。WSLの成功をWindows実機成功の代替証拠にしない。

## 3. 実行

```bash
task dev
task process:daily
task sync
task web:dev
```

systemdの導入または更新:

```bash
task systemd:verify
task systemd:install
```

Windowsの導入:

```text
infra\windows\bootstrap.bat
```

外部watchdogの導入:

```powershell
powershell.exe -ExecutionPolicy Bypass -File infra/windows/install-vlog-watchdog.ps1
```

## 4. データ完全性

- raw evidenceを自動削除しない。
- 処理前の棚卸しは `scripts/phase0_inventory.py` を使う。
- file existenceをv2の正準処理状態にしない。
- Supabase object一覧は固定1000件で完了扱いにせず、ページング終了まで取得する。
- 公開は独立したPublicationDecisionを必要とする。

## 5. 復旧

1. `task status` とoperations reportで失敗component/resourceを特定する。
2. systemdならrendered unitとtemplate双方を確認する。
3. Windowsなら `data/logs/windows-bootstrap.log` と `%LOCALAPPDATA%\VLog\watchdog.log` を確認する。
4. 同じsource hashとpipeline versionの重複実行を避ける。
5. 原因修正後に対象入口を再実行し、出力と監査eventを確認する。

## 6. 完了条件

- 実行対象のOS/サービスで検証した証拠がある。
- `task lint`, `task test`, `task doc:check` が通る。
- systemd変更は `task systemd:verify` が通る。
- Reader変更は `task web:build` が通る。
- [Git workflow](git.md)に従って変更を公開する。
