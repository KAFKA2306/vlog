# Infrastructure

Deployment and operations assets live here.

- `supabase/migrations/`: versioned PostgreSQL, RLS, Storage, and outbox migrations.
- `systemd/`: Linux/WSL units and installation helpers.
- `windows/`: Windows Task Scheduler, bootstrap, and watchdog assets.

Runtime paths must be derived from the repository root or explicit environment variables. Infrastructure files must not contain user-specific `/home/...` paths as portable defaults.
