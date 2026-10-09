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
