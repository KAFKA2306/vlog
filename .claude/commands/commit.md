# Commit

Inspect and stage only the intended paths, then commit and push with the supplied message.

```bash
git status --short
git diff
git add <explicit-paths>
git diff --cached
git commit -m "$ARGUMENTS"
git push
```

Follow [the repository Git workflow](../../.agent/workflows/git.md). Never substitute `git add .` for scope review.
