# VLog 仕様

VLogは、VRChatなどで起きたことを記録し、あとから確認・訂正・検索・日記化・公開できるようにするシステムです。

## 1. 何をするか

```text
記録する
音声・写真・動画・会話
    ↓
記憶として整理する
いつ / 誰と / 何が起きた / 何を言った
    ↓
利用する
日記 / 物語 / 画像 / 検索
    ↓
必要なものだけ公開する
KafLog
```

内部では次の名前を使います。

| 人間向けの説明 | 内部名称 |
|---|---|
| 元の記録 | Evidence |
| 確認できる記憶 | Human Memory |
| 日記・物語・画像など | Narrative Artifact |
| 公開を承認したもの | Public Projection |

## 2. 必ず守ること

1. 元の証拠を、AI生成文で置き換えない。
2. AIが生成した内容を、自動で事実や記憶として確定しない。
3. 採用した記憶から、根拠となるEvidenceへ遡れるようにする。
4. 訂正では過去の値を消さず、revisionを追加する。
5. 記憶として採用する判断と、公開する判断を分離する。
6. raw evidenceはprivateを既定とする。
7. Graphiti、pgvectorなどの検索用データは再生成可能なprojectionとして扱う。

## 3. どこに保存するか

| 保存先 | 責務 |
|---|---|
| Private object storage | 原音声、写真、動画、全文transcriptなどのEvidence byte列 |
| PostgreSQL / Supabase | source metadata、episode、claim、revision、ingestion state、publication decision |
| Private memory repository | 人間がreviewしたjournal、policy、correction、長期的なmemory view |
| Public site | 明示的に公開を承認したprojectionのみ |

公開GitHub repositoryは、private evidenceや個人のmemory dataの正準storeにしません。

## 4. 現在動いている処理

現在のruntimeは移行期間中のためfile-basedです。

```text
VRChat processを検知
    ↓
録音
    ↓
文字起こし
    ↓
日記・物語・画像などを生成
    ↓
選択した出力をSupabaseへ同期
    ↓
Next.js Reader / KafLogで表示
```

file existenceやdirectory scanによる処理状態はlegacy mechanismです。最終状態では、stable ID、content hash、明示的なingestion state、outboxへ移行します。

## 5. 動作保証

ここでいう「保証」は、絶対に障害が起きないという意味ではありません。**変更ごと・定期的に機械検証し、合格した範囲だけを動作確認済みと扱う**という意味です。

### A. Repository保証 — pull request / main更新ごと

`.github/workflows/test.yml` が次を検証します。

- Python sourceがcompileできる
- Ruff lint / format check
- public/private repository boundary
- companion browser/runtime contract parity
- systemd unit templateの構文
- Python tests
- Reader unit tests
- Reader typecheck / lint / build
- test後にcheckoutが汚れていない

これらのいずれかが失敗したcommitは、repository-levelで動作確認済みとは扱いません。

### B. Reader表示保証 — Reader変更ごと

`.github/workflows/reader-visual-regression.yml` が固定fixtureを使い、desktop/mobileの代表画面を実際に起動してscreenshotを取得し、承認済みbaselineとpixel比較します。

対象にはhome、Diary、Novel、People Said、Timelineを含みます。

### C. Public production保証 — 1時間ごと

`.github/workflows/production-smoke.yml` が `https://kaflog.vercel.app` を外部から確認します。

- `/api/health` がHTTP成功を返す
- `status = ok`
- `environment = production`
- `gitCommitRef = main`
- deployment commit SHAが取得できる
- `/`
- `/timeline`
- `/novels`
- `/people-said`

主要routeのいずれかがHTTP成功を返さない場合、その時点のpublic productionは動作確認済みとは扱いません。

### D. 実機でのみ保証できるもの

GitHub-hosted CIでは次を保証できません。

- 実際のVRChat process検知
- 実audio deviceからの録音
- GPUを使った文字起こし
- Windows Task Schedulerの実稼働
- production hostのsystemd enable/restart/recovery
- live Supabase data、RLS、Storage policyの正しさ
- private object storageへの全Evidence移行

これらは対象hostで実行したE2E evidenceがある場合だけ「実機確認済み」とします。repositoryにscriptやtemplateが存在するだけでは合格にしません。

## 6. 完了の判定

機能は、該当する保証レイヤーがすべてgreenで、未検証のenvironment依存項目が明示されている場合だけ完了扱いにします。

```text
codeを書いた
  ≠ 完了

testがgreen
  = repository内で確認済み

production smokeもgreen
  = public Readerまで確認済み

実機E2Eもgreen
  = そのhost/runtimeまで確認済み
```

## 7. 正準文書

- この文書: 製品仕様と動作保証
- `docs/architecture/human-memory-v2.md`: target architectureとmigration
- `docs/architecture.md`: 現行runtime architecture
- `docs/OPERATIONS.md`: 運用手順
- GitHub Issue: 未完了作業と検証証拠

仕様、実装方法、進捗を同じ文書で混同しません。

## 8. 外部仕様

GitHub Actionsのworkflowとrun historyはGitHub公式仕様に従います。

- https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions
- https://docs.github.com/en/actions/how-tos/monitor-workflows/view-workflow-run-history
