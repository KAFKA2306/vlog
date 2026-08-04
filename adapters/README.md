# Adapters

Vendor- and storage-specific implementations live here.

- `postgres/`: canonical metadata persistence, transactions, outbox, FTS, pgvector, and RLS.
- `supabase-storage/`: private object storage and explicit public projection buckets.
- `graphiti/`: rebuildable temporal relationship projection.
- `cognee/`: optional rebuildable knowledge projection.
- `qdrant/`: optional vector index for scale beyond the PostgreSQL operating envelope.

Graphiti, Cognee, pgvector, and Qdrant are projections. None may become the sole source of truth for evidence, claims, revisions, or publication decisions.
