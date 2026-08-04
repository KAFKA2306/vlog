# Git workflow

## Scope

1. Inspect `git status --short` and `git diff`.
2. Separate unrelated work before staging.
3. Stage explicit paths only.
4. Use a factual commit message that describes the complete logical change.

```bash
git add path/to/file another/path
git diff --cached
git commit -m "docs: consolidate runtime documentation"
```

Do not use `git add .` or conceal unrelated changes in the same commit.

## Verification

Run the checks relevant to the change before push:

```bash
task lint
task test
task doc:check
```

Add `task systemd:verify` for systemd changes and `task web:build` for Reader changes. Review the diff again because formatting tasks may modify files.

## Publication

Push the intended branch, open a pull request, wait for required checks, and merge only when the PR head is unchanged and the validation evidence matches the claimed scope. Do not describe CI as proof of live infrastructure behavior.
