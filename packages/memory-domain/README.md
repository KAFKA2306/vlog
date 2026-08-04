# memory-domain

Storage-agnostic canonical entities for Human Memory Repository v2.

## Owns

- `SourceObject`, `Episode`, `Utterance`, `Moment`, and `Entity`
- `MemoryClaim` and append-only `MemoryRevision`
- generated `Artifact` metadata
- explicit `PublicationDecision`
- ingestion idempotency identity (`source_hash + pipeline_version`)

## Does not own

- filesystem or Supabase access
- embeddings, Graphiti, Cognee, or Qdrant indexes
- prompt templates and model clients
- public web rendering
- private journal content

An accepted `MemoryClaim` cannot be constructed without provenance evidence. The domain package therefore makes the central v2 rule executable rather than documentary.
