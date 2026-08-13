# ingestion

Status: foundation implemented.

Responsibility: inventory, deterministic source inspection, and future ingestion/idempotency capabilities. Provider-specific persistence and application-specific publication do not belong here. See [Human Memory v2](../../docs/architecture/human-memory-v2.md).

## Social Mirror dry-run backfill

`social_mirror_backfill.py` inspects immutable source records without persisting `MemoryClaim` objects.

Safety rules:

- `raw_transcript` can become a `verified_quote_candidate` only when the source already provides an `other` speaker boundary plus a canonical `utterance_id`; the exact raw utterance is then checked with the Social Mirror evidence validator.
- `raw_transcript` with an unknown speaker boundary or missing utterance trace remains a `review_candidate`.
- `summary` and `diary` quote markers are always `review_candidate`; quotation marks in derived prose never promote content to `direct_quote`.
- self speech is skipped.
- every inspected item receives an explicit reason.
- candidate IDs are SHA-256-derived from immutable source/candidate material, so the same dry-run is deterministic.
- optional start/end dates are inclusive.
- the CLI prints JSON only; it has no canonical persistence or publication dependency.

Example:

```bash
python scripts/social_mirror_backfill.py \
  --input path/to/source-manifest.jsonl \
  --start-date 2026-08-01 \
  --end-date 2026-08-13
```

Input JSONL records distinguish `source_kind` (`raw_transcript`, `summary`, `diary`) and carry provenance IDs. Raw transcript records may additionally provide `utterance_id`, `speaker_kind` (`self`, `other`, `unknown`), and a non-identifying `speaker_label`.
