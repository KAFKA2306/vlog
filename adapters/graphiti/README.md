# Graphiti projection adapter

Rebuildable temporal projection of canonical Episodes into Graphiti. Graphiti is never canonical; deleting its data loses nothing that a re-run cannot restore.

## Boundary

- Input is `EpisodeCandidate` (canonical Episode, Utterances, Claims, `source_hash`, `pipeline_version`). Summary, novel, MBTI and psychological interpretation are not inputs.
- `vlog_memory_domain.projection` owns the payload, `projection_key = sha256(episode_id, source_hash, pipeline_version, projection_version)`, skip/reject rules, audit counts, and failure isolation. It imports no Graphiti SDK.
- This package owns the Graphiti mapping (`GraphitiProjectionSink`), a JSONL projection ledger, and trace resolution.
- 1 session = 1 Graphiti episode, `reference_time` = episode start, deterministic graph UUID from `projection_key`.
- Only `ACCEPTED` claims with evidence inside the same episode become facts. Low-information episodes are skipped; evidence-inconsistent ones are rejected.
- Sink failures are recorded in the ledger and never reach canonical processing; re-running retries only unprojected keys.
- `run_projection(..., dry_run=True)` is the backfill preview: no sink or ledger writes.
- `resolve_trace(ledger, graph_uuid_or_episode_name)` returns the canonical episode id, `source_hash` and `EvidenceRef`s.

## Status

Implemented in repository and fake-tested. Not wired to the daily pipeline (canonical persistence is Human Memory v2 Phase 3). `build_graphiti_client` lazily imports `graphiti_core`, which is not a declared dependency; live Graphiti behavior is UNVERIFIED.
