# Windows CMD/PS1 Error Map (VLog)

## 1. `UNC パスはサポートされません`
- 条件: `\\wsl.localhost\...` をカレントにして `cmd.exe` 起動
- 影響: 作業ディレクトリが `C:\Windows` にフォールバックし、相対パスが破綻
- 対応:
  - `pushd \\wsl.localhost\Ubuntu-22.04-LTS\home\kafka\vlog\windows`
  - もしくはローカルコピー先から起動

## 2. `用語 'cargo' は認識されません`
- 条件: Windows `PATH` に `.cargo\\bin` がない
- 確認:
  - `where.exe cargo`
  - `Test-Path "$env:USERPROFILE\\.cargo\\bin\\cargo.exe"`
- 対応:
  - `bootstrap.ps1` で `cargo.exe` を絶対パス解決

## 3. `ファイル名、ディレクトリ名、またはボリューム ラベルの構文が間違っています`
- 条件: `cmd /c` へ渡す `cd /d` 引数や引用符が不正
- 対応:
  - `ProviderPath` を使ってパス文字列を正規化
  - launch 文字列の二重引用を監査

## 4. `run.bat` が即終了
- 条件: bootstrap 内で例外を捕捉せず終了
- 対応:
  - bootstrap 用ログと monitor 用ログを分離
  - `try/catch` で例外をログ化して再試行
  - 多重起動を Mutex で防止

## 5. 強制終了後に勝手に終了扱いになる
- 条件: 旧プロセス残骸、ログロック、同名プロセス競合
- 対応:
  - Linux 側 `pkill` 実行
  - Windows 側 `Stop-Process -Force`
  - 完全停止を確認してから再起動

## 6. 権限/ExecutionPolicy で起動しない
- 確認:
  - `Get-ExecutionPolicy -List`
  - `Get-Item .\src\windows\rust\bootstrap.ps1 | Unblock-File`
- 対応:
  - ユーザースコープで許可
  - 署名要件がある環境では署名済みスクリプトへ統一
