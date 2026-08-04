# Command rules

`Taskfile.yaml` is the command index. Read the task definition before relying on a command name or side effect.

Common repository checks:

```bash
task lint
task test
task doc:check
task systemd:verify
task web:build
```

Operational and deployment commands may modify the host or contact external services. Execute them only in the intended environment and report their actual result separately from CI.
