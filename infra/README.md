# Infrastructure

Deployment and operations assets live here.

- `infra/supabase/migrations/`: versioned PostgreSQL, RLS, Storage, and outbox migrations.
- `infra/systemd/`: Linux/WSL units and installation helpers.
- `infra/windows/`: Windows Task Scheduler, bootstrap, and watchdog assets.

Runtime paths must be derived from the repository root or explicit environment variables. Infrastructure files must not contain user-specific `/home/...` paths as portable defaults.
