# Use-case layer

Use cases coordinate domain protocols and infrastructure adapters for capture, transcription, generation, evaluation, synchronization, and current daily processing.

- Keep orchestration separate from provider implementation.
- Preserve source identity and failure context across steps.
- Avoid duplicate work using the best available current state, while recognizing that file existence is not the final v2 idempotency model.
- Do not combine generation success with publication approval.
- Add focused tests for success, failure, replay, and partial-output behavior.

The implementation and tests are authoritative for current callable names.
