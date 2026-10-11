# memory-domain

Status: foundation implemented.

Responsibility: canonical entity and provenance invariants. Provider-specific code and application wiring do not belong here. See [Human Memory v2](../../docs/architecture/human-memory-v2.md).

## Social Mirror evidence contract

Social Mirror does not introduce another canonical store. A Social Mirror observation remains a normal `MemoryClaim` with `claim_type="social_mirror"`, canonical `EvidenceRef` provenance, and a typed `SocialMirrorValue`.

Evidence levels are deliberately non-interchangeable:

- `direct_quote`: exact text must occur in a referenced raw `Utterance` whose episode matches the `EvidenceRef`.
- `paraphrase`: evidence-backed speech content without a claim of verbatim wording.
- `inferred_impression`: an interpretation only; `is_spoken_fact` is always false.

A quotation mark in a summary, Diary, Novel, or other derived artifact is not sufficient to promote content to `direct_quote`. Unknown speakers remain `speaker_label="unknown"` unless independent identity evidence exists.

`validate_social_mirror_claim()` is the dereferencing evidence gate because JSON Schema can validate shape and provenance presence but cannot inspect external raw utterance text.

## Interaction contract

Self emotion, interpersonal utterances, explicit responses, and relationship state are normal `MemoryClaim` records (`self_emotion`, `interaction_utterance`, `interaction_response`, `relationship`) with typed values in `interaction.py`; there is no second relationship store.

- AI-inferred emotion and inferred inner state of another person can only be `candidate`.
- Speaker/target use `IdentityState`; non-confirmed identities carry no entity id.
- Claim ids are deterministic over type, subject, evidence, and value, so `ingest_claims()` is idempotent and rejects conflicting content under one id.
- `revise_relationship()` returns a successor claim and a `MemoryRevision`; the prior claim is never modified.
- `retrieve_person_timeline()` projects claims and revisions chronologically. `vlog_privacy.project_interaction_claim()` publishes nothing without an explicit decision and omits entity ids and evidence.

Contract tests use only the synthetic `tests/fixtures/human_memory_interaction.json`, which is not a record of real interactions. Actual private-evidence E2E: NOT_RUN / UNVERIFIED.
