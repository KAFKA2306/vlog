# Architecture decision records

ADRs preserve why a decision was made. They do not override current code, configuration, or later ADRs.

| ADR | Decision | Audit status |
|---|---|---|
| [0001](0001-introduce-harness-engineering.md) | harness engineering | accepted; implementation evolved |
| [0002](0002-autonomous-maintenance-principles.md) | autonomous maintenance principles | partially superseded by explicit safety gates |
| [0003](0003-transcription-as-thought-noise-compression.md) | transcription as a derived cognitive aid | accepted; not canonical evidence replacement |
| [0004](0004-resource-protection-for-gpu-stability.md) | resource-aware heavy processing | accepted; current schedule is separate |
| [0005](0005-prompt-vault-integration.md) | external prompt asset integration | accepted for prompts; not canonical memory |
| [0006](0006-automated-image-optimization.md) | generated-image optimization | accepted; old performance figures are historical |
| [0007](0007-zero-trust-harness.md) | runtime incident evidence | accepted |
| [0008](0008-systemd-security-and-observability.md) | portable systemd supervision | accepted; live installation requires host verification |
| [0009](0009-whisper-model-optimization.md) | transcription model selection | accepted; current config is authoritative |
| [0010](0010-external-reader-integration.md) | external Reader integration | accepted; current root is `apps/reader/` |
| [0011](0011-systemd-daily-timer-6am-jst.md) | daily timer changed to 09:00 | accepted; host timezone must be verified |

Each ADR contains an audit note dated 2026-08-04. Historical measurements remain historical unless a reproducible current benchmark is cited.
