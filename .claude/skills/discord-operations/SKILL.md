---
name: discord-operations
description: Operate and audit VLog Discord notifications without exposing private data.
---

# Discord operations

Use `DISCORD_WEBHOOK_URL` from the environment and the notification entry points implemented by the runtime. Never print or commit the webhook.

- Keep notifications brief and free of transcripts, raw evidence, secrets, home paths, and full journal excerpts.
- Diagnose failures through structured local events and systemd journal before sending a summary.
- Verify failure notifications in the actual host environment; repository tests cannot prove webhook delivery.
- Treat notification failure as an observable secondary failure, not as proof that the primary operation failed or succeeded.

See [operations](../../../docs/OPERATIONS.md) and [systemd assets](../../../infra/systemd/README.md).
