# Markdown governance

Markdownはrepository contractの一部です。各文書は1つの明確な責務だけを持ち、current behavior、target architecture、historical evidence、volatile statusを混同しません。

## Ownership classes

| Class | Location | Rule |
|---|---|---|
| repository entry | `README.md` | purpose、minimal setup、canonical routesのみ |
| product contract | `docs/SPEC.md` | product invariants、storage/publication boundary、verification / completion contract |
| documentation map | `docs/README.md` | authority、precedence、status vocabulary |
| orientation | `docs/overview.md` | short non-normative overview。status / parallel specを保持しない |
| architecture / contracts | `docs/architecture*`, `docs/*contract.md` | currentまたはtarget stateを明示して記述 |
| operations / maintenance | `docs/OPERATIONS.md`, `docs/MAINTENANCE.md`, `docs/operations/` | executable runbookとrepeatable procedure |
| component docs | component `README.md` | local boundaryとentry pointだけ |
| decisions | `docs/adr/` | decision rationaleと明示的audit status |
| incidents | `docs/incidents/` | dated evidence。current statusとして使わない |
| agent routers | `AGENTS.md`, `.agent/`, `.claude/`, `.gemini/` | canonical docsへの短いrouting |
| tool memory | `.serena/` | pointerのみ。production statusやprivate memoryを保持しない |

Generic tutorial、theme library、communication template、unrelated language-maintenance guideをproduct documentationとして追加しません。

## Authority rules

- Product ruleを変更するときは`docs/SPEC.md`を更新し、README / overviewへコピーしない。
- Current runtime structureは`docs/architecture.md`、target architectureは`docs/architecture/human-memory-v2.md`へ分離する。
- Commandは`Taskfile.yaml`、package / Python requirement / console entry pointはmanifest、model selectionはconfiguration / consuming codeをauthorityとする。
- Point-in-time progressはGitHub Issue / PR、live stateはactual environment evidence、dated incidentは`docs/incidents/`へ置く。
- Generated narrative / illustration / graph / vector dataはderived artifactとして明示する。
- Completion claimはrepository、CI、environment evidenceを分離する。

## Content rules

- Retained MarkdownはH1とdefined purposeを持つ。
- Repository-relative Markdown linkを使用し、targetが存在することを確認する。
- Frontmatter内のrepository pathもcurrent treeと一致させる。
- Personal home path、drive-specific path、`file://` link、secretを残さない。
- Volatile dependency version、task inventory、temporary service statusを複製しない。
- Component READMEは上位system specificationを再記述しない。
- Agent fileはcanonical docsへrouteし、parallel specificationを作らない。

## Refactor rule

重複を見つけた場合は、新しいsummary documentを追加するのではなく次の順で整理します。

1. authorityを決める;
2. authorityへ必要な内容を残す;
3. duplicate documentをpointerへ縮約するか削除する;
4. stale path / command / status snapshotをcurrent implementationへ照合する;
5. linkとrepository boundaryをmachine checkする。

## Validation

```bash
task doc:check
```

Current checkはrequired repository boundaries、local Markdown links、portable paths、H1、retired document、active agent instruction sizeを検証します。Passing resultはrepository consistencyだけを示し、external URLやlive infrastructureを検証しません。
