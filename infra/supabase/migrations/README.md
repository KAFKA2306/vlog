# Supabase migrations

Versioned PostgreSQL, RLS, Storage policy, idempotency, and outbox migrations belong here.

Phase 0 exports the current remote state before any migration is applied. Public/private separation must be enforced by database and Storage policy, not only by application branches.
