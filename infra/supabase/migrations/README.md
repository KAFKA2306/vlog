# Supabase migrations

This directory is the repository source of truth for ordered SQL migrations of the current Supabase projection. Do not maintain a second snapshot schema in parallel.

Human Memory v2 canonical migrations, outbox, and complete RLS/Storage policy migration remain future work.

Export schema, rows, policies, buckets, and paginated object manifests before destructive changes. See [maintenance](../../../docs/MAINTENANCE.md).
