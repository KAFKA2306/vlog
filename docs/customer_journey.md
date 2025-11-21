# Customer Journey (Windows 11)

- 1回だけ: 管理者PowerShellでリポジトリ直下に移動し `.\bootstrap.ps1` 実行 → GOOGLE_API_KEY 入力 → マイク許可を承認。
- 普段: ログオンするだけ。VRChatを起動すると自動録音し、終了後に自動で文字起こし・要約まで進む（ウィンドウは出ない）。
- 成果の置き場: 音声は `recordings/`、生テキストは `transcripts/`、日記は `summaries/`、動作ログは `vlog.log`。
- 停止したい時: タスク スケジューラで「VlogAutoDiary」を無効化または削除。
- GPUを使う場合（任意）: 環境変数 `VLOG_WHISPER_DEVICE=cuda` と `VLOG_ALLOW_UNSAFE_CUDA=1` を設定してから再ログオン。
