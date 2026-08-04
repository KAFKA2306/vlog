# 日次パイプライン契約

## 目的

日次パイプラインは、未処理の録音から公開可能な日記成果物までを自動で前進させ、同期と通知を完了する。

## 実行契約

| 項目 | 定義 |
| :--- | :--- |
| 実行主体 | vlog-daily.timer が vlog-daily.service を起動する |
| 実行時刻 | 毎日 09:00 JST。未実行分は次回 WSL 起動時に Persistent=true で実行する |
| 実行入口 | task process:daily |
| 前提条件 | .env、uv.lock、GPU、録音・成果物ディレクトリが利用可能である |
| 成功条件 | 日次コマンドが終了コード 0 で完了し、systemd journal に成功結果が残る |
| 失敗条件 | 任意の必須処理が非ゼロ終了し、vlog-daily-failure.service が通知を送る |

## 処理順序

1. VRChat、GPU VRAM、CPU 使用率、未処理件数を収集する。
2. 未処理録音があり、VRChat が停止中でリソースに余裕がある場合だけ文字起こしと日次成果物生成を実行する。
3. 文字起こし済みの日付から要約、小説、画像、評価の不足分を生成する。
4. Cognee キューを初期化し、設定されたバッチ件数を処理する。
5. Supabase 同期を実行する。
6. Discord に日次完了通知を送る。

## データ契約

| 入力 | 出力 |
| :--- | :--- |
| data/recordings の WAV、FLAC、MP3 | data/transcripts の TXT |
| data/transcripts の TXT | data/summaries の summary TXT |
| data/summaries の summary TXT | data/novels の Markdown、data/photos の PNG |
| data/summaries と data/novels | data/evaluations の JSON |
| ローカル成果物 | Supabase、Cognee、Discord 通知 |

処理済み判定はファイル名に含まれる YYYYMMDD と対応成果物の存在で決定する。同じ入力に対する再実行では、存在する成果物を再利用し、不足分だけを生成する。

## 自動化の管理

    task up
    task status
    task monitor:daily
    task log:daily
    task down

ユニットテンプレートは `infra/systemd/*.in` を正とし、インストール時に現在のリポジトリパスを埋め込む。導入前に `task systemd:verify` で描画後の構文を検証する。

## 検証証拠

完了判定には次の証拠をすべて使用する。

1. task systemd:verify が成功する。
2. task status が Windows タスク、systemd ユニット、次回タイマー実行時刻を表示する。
3. journalctl --user -u vlog-daily.service に直近実行の終了結果がある。
4. 未処理録音に対応する transcript、summary、novel の不足件数が減少する。
5. task audit が失敗または未検証を報告しない。
