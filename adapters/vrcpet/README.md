# VRCPet / Muchio private observation adapter

This adapter ingests files produced by VRCPet/Muchio as a **private observation source** for Human Memory v2. It is an external-data boundary, not a second diary generator and not an extension of `packages/companion`.

## Boundary

- The VRCPet source directory is read-only. This adapter exposes no write/delete operation for it.
- The executable itself is not inspected, modified, or redistributed.
- Source roots are configurable and may be restricted by an explicit allowlist. A particular Windows path or filename layout is treated as an observed input layout, not as a vendor-guaranteed API.
- Windows absolute paths and user names are never copied into canonical manifests. Only source-relative paths are retained.
- Raw bytes are hashed with SHA-256 before normalization. Content-addressed deterministic UUIDs make identical observations idempotent.
- Conversation JSONL becomes `SourceKind.CONVERSATION`; profile, vocabulary, and operational state becomes `SourceKind.DOCUMENT`.
- `profile.json` and `heard_nouns.json` are companion state. They do not create or accept human `MemoryClaim` objects.
- Malformed lines and schema drift are isolated into parse/audit issues instead of being silently discarded.
- Exact state bytes can be handed to private persistence as immutable daily snapshot candidates. The public repository must never contain real private snapshot payloads.

## Supported observed inputs

```text
<configured-root>/
├─ logs/**/*.jsonl
├─ pet.log
├─ profile.json
└─ heard_nouns.json
```

The reader only discovers these names/patterns. Unknown vendor fields remain in the parsed record and therefore remain recoverable from the raw source.

## Flow

```text
read-only SourceFile
  -> tolerant parse
  -> SHA-256 + deterministic UUID
  -> SourceObject + source manifest
  -> IngestionRun(source_hash + pipeline_version)
  -> immutable profile/vocabulary snapshot candidate
  -> Episode association
  -> rebuildable companion daily view ("すいの目から見た1日")
```

`pipeline_version` belongs to `IngestionRun`; VRCPet-specific path/provenance details remain in manifest metadata. The existing `schemas/source-manifest.schema.json` contract is reused rather than introducing a VRCPet-specific canonical schema.
