# Windows環境ガイド

Windows環境でVLog Auto Diaryを実行するためのスクリプトとガイド。

## ファイル構成

### `bootstrap.bat`

初回セットアップ用スクリプト（管理者権限で実行）：

- `.env`ファイルの作成（`.env.example`からコピー）
- 必要なディレクトリ作成（`data/recordings`, `data/transcripts`, `data/summaries`, `data/archives`, `logs`）
- Windows用Python仮想環境（`.venv-win`）のセットアップ
- タスクスケジューラへの登録（ログイン時に自動起動）
- 初回起動

### `run.bat`

アプリケーション起動スクリプト：

- `.venv-win`の仮想環境を使用
- `python -m src.main` でアプリケーション起動
- ログは`logs/vlog.log`に出力

## 使い方

### 初回セットアップ

1. 管理者権限でコマンドプロンプトを開く
2. プロジェクトディレクトリに移動
3. `windows\bootstrap.bat` を実行

これにより、次回ログイン時から自動的にバックグラウンドで起動するようになります。

### 手動起動

`run.bat` をダブルクリック、またはコマンドプロンプトから実行：

```cmd
windows\run.bat
```

### 停止方法

タスクマネージャーでPythonプロセスを終了、または：

```cmd
taskkill /IM python.exe /F
```

## トラブルシューティング

### 1. ウィンドウがすぐに閉じてしまう

エラーが発生している可能性があります。`run.bat`と`bootstrap.bat`には`pause`コマンドが入っており、エラーメッセージを確認できます。

手動実行で確認：

```cmd
cd /d %~dp0..
.venv-win\Scripts\python.exe -m src.main
```

### 2. ネットワークドライブ（UNCパス）での実行

`\\server\share\path` のようなネットワークパス上で実行する場合、`cd`コマンドではディレクトリ移動できません。

スクリプト内では`pushd "%~dp0.."`を使用して一時的にドライブ文字を割り当てています。

推奨：ネットワークドライブを`Z:`などのドライブレターに割り当ててから実行。

### 3. Python環境

- Windows用の仮想環境：`.venv-win`
- WSL（Linux）側の仮想環境：`.venv`

**互換性がないため混同しないよう注意。**

### 4. ログの確認

実行ログは `logs/vlog.log` に出力されます。

```cmd
type logs\vlog.log
```

動作がおかしい場合は、まずこのファイルを確認してください。

### 5. 自動起動の解除

タスクスケジューラから手動で削除：

1. タスクスケジューラを開く（`taskschd.msc`）
2. `VLog Auto Diary` タスクを探す
3. 削除

## 環境変数

`.env`ファイルに以下を設定：

```env
GOOGLE_API_KEY=your_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

## データディレクトリ

```
data/
├── recordings/    録音ファイル（FLAC）
├── transcripts/   文字起こし結果（TXT）
├── summaries/     日記形式要約（TXT）
└── archives/      処理済み録音の移動先
```

## システム要件

- Windows 10/11
- Python 3.11以上
- 管理者権限（初回セットアップのみ）

