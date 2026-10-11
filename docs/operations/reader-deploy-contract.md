# Reader deploy contract

`apps/reader` のVercel production deployとrelease identityのcontractです。Issue #88が所有し、#66を統合します。

## Contract

| 項目 | 契約 | 実装authority |
|---|---|---|
| Project | `KafLog` (`prj_t52LlD6qx3zdzdgOqBomZBfzzwb6`、team `team_WAiNUdK4pWv6eK8LxnaVY1mC`)。別IDはdeployをrefuseする | `scripts/deploy_reader.py` |
| Root Directory | `apps/reader` | Vercel project setting (UNVERIFIED) |
| Deploy entry | `task web:deploy` / `production-deploy.yml` のみ。いずれも `scripts/deploy_reader.py` を呼ぶ | `Taskfile.yaml` |
| Project selection | `VERCEL_PROJECT_ID` / `VERCEL_ORG_ID` をscriptが固定値と照合。`.vercel/` linkはgitignore | `scripts/deploy_reader.py` |
| Source identity | clean working tree、branch `main`、`git rev-parse HEAD` の40桁SHAのみ。dirty / 他branchはdeployしない | `release_identity()` |
| Injection | `--env VLOG_DEPLOY_GIT_SHA/REF` と `--meta gitCommitSha/gitCommitRef` | `deploy()` |
| Health | `GET /api/health` が `gitCommitSha`, `gitCommitRef`, `deploymentId`, `environment` を返す。未設定は `null`(silent healthy扱いしない) | `apps/reader/app/api/health/route.ts` |
| Verification | status=ok、environment=production、`dpl_*`、40桁SHA、ref=main。期待SHAがあれば一致。空値・不一致はFAIL | `scripts/reader_identity.py` |
| Smoke | 1時間ごとに上記identityを検証し、SHAがcheckout内の実在commitに解決できることを確認 | `production-smoke.yml` |
| Secrets | `VERCEL_TOKEN` はGitHub secretのみ。Gitに保存しない | `production-deploy.yml` |

## Environments

- development: `task web:env` / `task web:dev`。Vercel deployではない。
- preview: Vercel preview env。`/api/health` の `environment` は `preview` であり、production smokeはPASSさせない。
- production: `--prod` deployのみ。`VERCEL_ENV=production`。

## UNVERIFIED (repositoryから観測不能)

- Vercel project Root Directoryが実際に `apps/reader` か。`deploy_reader.py` は現在 `apps/reader` をcwdにして `vercel` を実行する。Root Directoryが `apps/reader` に設定済みなら二重解決になりうるため、dashboard確認の上でcwdか設定のどちらかを1つに固定すること。
- development / preview / production のVercel env変数の分離状態。
- Vercel deployment metadata (`gitCommitSha` / `gitCommitRef`) とproduction `/api/health` の直接read-back。
- merge後 `main` のexact-head read-back。

これらはhuman操作またはreal deploy後の観測でのみclose条件を満たします。
