# ADR-0006: generated-image optimization

## Status

Accepted; audited 2026-08-04.

## Context

Generated illustrations can be unnecessarily large for Reader delivery. Optimization should reduce transfer cost without turning generated media into canonical evidence or silently changing publication state.

## Decision

Image optimization is a derived-artifact step. The original generation metadata, source association, and publication decision remain distinct from the optimized delivery representation.

Concrete codecs, dimensions, and compression settings are defined by the implementation and deployment requirements. Historical size reductions are not current benchmarks unless reproduced and recorded with the input set and tool versions.

## Consequences

- Reader delivery can use optimized representations.
- Optimization failure must remain visible and must not delete the only retained artifact.
- Public delivery files must not expose private source media or unrestricted object URLs.

## References

- [Illustration generation](../image.md)
- [Reader](../../apps/reader/README.md)
