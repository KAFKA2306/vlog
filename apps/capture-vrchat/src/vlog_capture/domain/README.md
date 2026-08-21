# Domain layer

The domain defines provider-independent entities, protocols, audit concepts, and publication rules used by the current application.

- Do not import Supabase, model SDKs, systemd, Windows, Next.js, or application wiring.
- Represent invalid states through types and explicit invariants where practical.
- Keep evidence, generated artifacts, and publication decisions distinct.
- Preserve provenance and correction history when bridging to Human Memory v2 packages.

The implementation and tests are authoritative for current symbols.
