# privacy

Status: foundation implemented for Social Mirror publication.

Responsibility: redaction, pseudonymization, retention, and publication gates. Provider-specific code and application wiring do not belong here. See [Human Memory v2](../../docs/architecture/human-memory-v2.md).

## Social Mirror publication boundary

Social Mirror claims are private by default. Storing an evidence-backed claim does not grant publication approval.

The publication decision records two independent dimensions:

- `publish_text`: whether the reviewed quote/paraphrase/inference text may enter the public projection.
- `publish_speaker_identity`: whether the stored speaker label may accompany that text publicly.

Both default to `false`. A public projection is not produced unless `publish_text` is explicitly true.

The projection function accepts an already-canonical `MemoryClaim` plus its publication decision. It does **not** accept raw transcript text, source excerpts, storage clients, or entity lookup services. Public projection records therefore contain only the claim ID, publication-decision ID, evidence level, approved text, optional approved speaker label, and publication time.

Unknown speakers remain `unknown`; this layer never resolves an unknown speaker or an internal entity UUID into a guessed public identity.

Only accepted canonical Social Mirror claims may be projected. The publication decision retains `claim_id`, so every public projection can be traced back to the reviewed claim without exposing its raw evidence.
