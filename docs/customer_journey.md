# Customer Journey (Windows 11)

- 初回セットアップ: 管理者 PowerShell でリポジトリ直下に移動し `.\bootstrap.ps1` を実行（UNC の場合は一行で `powershell -NoProfile -ExecutionPolicy Bypass -File "\\wsl.localhost\\Ubuntu-22.04\\home\\kafka\\projects\\vlog\\bootstrap.ps1"` などと指定）→ GOOGLE_API_KEY を入力 → マイク許可を承認。
- ふだんの起動: ログオンするだけ（タスク スケジューラが `run_silent.vbs` → `run.cmd` → `run.ps1` を自動起動）。
- 手動で起動したい場合: PowerShell で `.\run.ps1`、CMD/ダブルクリックなら `run.cmd`。
- UNC/WSL パスで CMD を使うときは `run.cmd` が `pushd` してから PowerShell を呼ぶ。失敗する場合は PowerShell で `.\run.ps1` を実行。
- 成果物: 音声 `recordings/`、生テキスト `transcripts/`、日記 `summaries/`、動作ログ `vlog.log`。
- トラブル確認: `task status` で現在の処理状態を確認。
- 停止したいとき: タスク スケジューラで「VlogAutoDiary」を無効化または削除。
- GPU を使う場合（任意）: `VLOG_WHISPER_DEVICE=cuda` と `VLOG_ALLOW_UNSAFE_CUDA=1` を設定してから再ログオン。
