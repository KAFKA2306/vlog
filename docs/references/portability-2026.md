# 2026 portability primary references

Checked: 2026-08-20.

These links are rationale/reference material. VLog's normative decisions live in [`../architecture/portability.md`](../architecture/portability.md) and ADR-0012; external documentation is not copied as repository policy.

| Area | Primary documentation |
|---|---|
| Windows/WSL filesystem placement | Microsoft: https://learn.microsoft.com/en-us/windows/wsl/filesystems |
| Windows file/path naming | Microsoft: https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file |
| Windows long paths | Microsoft: https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation |
| Scheduled Task action/working directory | Microsoft: https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtaskaction |
| PowerShell `$PSScriptRoot` | Microsoft: https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_automatic_variables |
| Git text/EOL attributes | Git: https://git-scm.com/docs/gitattributes |
| Cross-platform/foreign path parsing | Python `pathlib`: https://docs.python.org/3/library/pathlib.html |
| Linux config/state/cache layout | XDG Base Directory: https://specifications.freedesktop.org/basedir-spec/latest/ |
| Cross-platform application directories | platformdirs: https://platformdirs.readthedocs.io/ |
| Python monorepo/workspaces | uv: https://docs.astral.sh/uv/concepts/projects/workspaces/ |
| Settings/env precedence | Pydantic Settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/ |
| Task platform/task schema | Task: https://taskfile.dev/docs/reference/schema |
| GPU transcription/NVIDIA Python libraries | faster-whisper: https://github.com/SYSTRAN/faster-whisper |
| GitHub runner/workspace variables | GitHub Actions: https://docs.github.com/en/actions/reference/variables-reference |
| Reproducible development container | Dev Container spec: https://github.com/devcontainers/spec |
| Vercel monorepos | Vercel: https://vercel.com/docs/monorepos |
| Supabase database migrations | Supabase: https://supabase.com/docs/guides/deployment/database-migrations |

When a recommendation changes materially, update the VLog decision only after re-checking the relevant primary documentation and validating the repository/host behavior it affects.
