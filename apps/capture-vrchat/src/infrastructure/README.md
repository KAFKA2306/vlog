# Infrastructure layer

Infrastructure implements current external boundaries: process and audio access, transcription and generation providers, local files, Supabase synchronization, settings, logging, graph projections, and system integration.

- Read `data/config.yaml`, environment variables, and settings code for current values.
- Add timeouts, retries, cleanup, and exception translation only where safe and observable.
- Do not convert a provider response or search index into canonical memory.
- Keep secrets out of logs and public artifacts.
- Verify network, GPU, audio, database, and operating-system behavior in their actual environments.

See [operations](../../../../docs/OPERATIONS.md).
