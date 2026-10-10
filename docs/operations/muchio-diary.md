# Muchio logs → diary → KafLog

VRCPet の日別 JSONL から既存プロンプトで日記を作ります。原文を GitHub、Vercel、Supabase に直接置きません。

## 1. ローカルで日記生成

次のコマンドは data/logs にある日別 JSONL を読み、非公開の下書きを data/muchio_diaries に生成します。

~~~bash
uv run --frozen python scripts/muchio_diary.py generate \
  --logs-dir data/logs --output data/muchio_diaries
~~~

Windows ログを WSL から読む場合は --logs-dir に /mnt/c/Users/front/AppData/Roaming/VRCPet/data/logs を指定します。ホスト設定 vrcpet.yaml の logs_dir が正しければオプションは省略できます。

生成には既存の data/prompts.yaml の summarizer.template と、設定済みの Gemini API が使われます。モデルへ入力文を送信する点に注意してください。

生成物は YYYY-MM-DD.md と YYYY-MM-DD.json です。後者には元ログ、プロンプト、日記本文の SHA-256 と件数、公開状態が含まれます。同じ入力とプロンプトは再生成しません。会話テキストを抽出できない日はスキップします。

ローカル LLM の下書き（data/private/nikki）を同じ形式へ移す場合は、1日ずつ次を実行します。下書きの注意書きと見出しを除き、本文とマニフェストを data/muchio_diaries に書きます。既存ファイルは上書きしません。

~~~bash
uv run --frozen python scripts/nikki_local.py --export --date 2026-10-09
~~~

## 2. 出力日記をレビュー

~~~bash
cat data/muchio_diaries/2026-10-09.md
sha256sum data/muchio_diaries/2026-10-09.md
~~~

人物、発言、私的情報、誤推定がないか確認し、必要なら日記を修正します。修正後、レビュー済みの本文ハッシュを確定します。

~~~bash
uv run --frozen python scripts/muchio_diary.py review \
  --date 2026-10-09 --output data/muchio_diaries
~~~

このコマンドはローカルのマニフェストを更新するだけで、公開しません。返された SHA-256 を次の publish に指定します。

## 3. レビュー済みの日付だけ公開

~~~bash
uv run --frozen python scripts/muchio_diary.py publish \
  --date 2026-10-09 \
  --sha '<レビュー済み日記の完全な SHA-256>' \
  --output data/muchio_diaries
~~~

ホストに VLOG_SUPABASE_URL と VLOG_SUPABASE_SERVICE_ROLE_KEY が設定されている必要があります。鍵は公開リポジトリやターミナルの共有ログに含めないでください。

この公開操作は Supabase daily_entries の同日1件に is_public=true を設定します。同日に別の日記が存在すると重複を避けるため停止します。

KafLog Reader は Supabase の公開日記を読むため、日記追加そのものに Vercel の再ビルドは通常不要です。公開後は https://kaflog.vercel.app/day/2026-10-09 を実際に確認してください。本番Readerの古いデプロイ問題は別途解消する必要があります。

## 原則

- 元 JSONL、非公開プロンプト入力、未承認の下書きは公開しない
- 一括 vlog sync を公開承認の代わりにしない
- generate はローカル生成のみ、publish は明示的な公開操作
- 生成日記には誤記や第三者の私的内容が含まれ得るため、公開前に本文を確認する
