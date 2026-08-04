# Windows 環境ガイド

Windows は VRChat プロセスの検知と録音を担当し、WSL は日次処理と成果物生成を担当する。Windows と WSL は同じリポジトリの data ディレクトリを共有する。

## 初回セットアップ

管理者権限のコマンドプロンプトでプロジェクトルートから実行する。

    infra/windows/bootstrap.bat

bootstrap.bat は次を実行する。

1. .env.example から .env を作成する。
2. data/recordings、data/transcripts、data/summaries、data/archives、data/logs を作成する。
3. .venv-win に uv.lock 固定の依存関係を同期する。
4. VlogAutoDiary をローカル cmd.exe 経由のログオン時タスクとして登録する。
5. 異常終了時は 1 分後に再起動するよう設定する。
6. 登録したタスクを起動する。

.env には実値を設定してから起動する。

## 手動起動

    infra/windows/run.bat

run.bat は UNC パスを一時ドライブへ割り当て、.venv-win と Python 3.12 と `apps/capture-vrchat` を含む `PYTHONPATH` で `src.main` を実行する。相対パスは必ずプロジェクトルート基準で解決される。依存関係は uv.lock から変更しない。

## 状態確認

Windows タスクの状態を確認する。

    schtasks /Query /TN VlogAutoDiary /V /FO LIST

WSL 側から全体状態を確認する。

    task status

正常時は次を満たす。

- VlogAutoDiary が Running である。
- Windows に uv.exe と .venv-win/Scripts/python.exe のプロセスが存在する。
- VRChat 起動後に data/recordings へ 44 バイトを超える FLAC が作成される。
- data/logs/windows-bootstrap.log に起動パスが記録される。
- data/logs/vlog.log に Application started と録音開始・停止が記録される。

## ログ

    Get-Content data/logs/windows-bootstrap.log -Tail 50
    Get-Content data/logs/vlog.log -Tail 50

windows-bootstrap.log は起動ごとに初期化され、起動時刻、解決済みパス、作業ディレクトリ、異常終了時の終了コードを記録する。

## 停止と再起動

    schtasks /End /TN VlogAutoDiary
    schtasks /Run /TN VlogAutoDiary

自動起動を無効化する場合はタスクスケジューラで VlogAutoDiary を無効化する。

## トラブルシューティング

### タスクが Running なのに録音されない

1. data/logs/windows-bootstrap.log の exit_code を確認する。
2. data/logs/vlog.log の最新 Application started を確認する。
3. Get-Process VRChat で Windows 側の VRChat を確認する。
4. data/recordings の最新 FLAC のサイズと更新時刻を確認する。

### 依存関係が再現できない

uv.lock と pyproject.toml を同期した状態で再実行する。

    set UV_PROJECT_ENVIRONMENT=.venv-win
    set UV_LINK_MODE=copy
    set UV_PYTHON=3.12
    uv sync --frozen

### UNC パスで起動できない

bootstrap.bat を管理者権限で再実行する。タスクはローカルの cmd.exe を起動し、run.bat 内の pushd が UNC を一時ドライブへ変換する。タスクの直接実行先に UNC 上の run.bat を指定しない。
