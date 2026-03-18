# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**VLog** is an automated VRChat experience logging system that:
1. Records audio when VRChat is running (via `system.py` process monitor)
2. Transcribes using Faster Whisper (large-v3-turbo, int8 quantization)
3. Generates summaries and novels using Gemini 2.5 Flash
4. Creates AI-generated artwork from narrative content
5. Syncs everything to Supabase PostgreSQL for a web interface

### Key Tech Stack
- **Backend**: Python 3.11+, Pydantic models, Protocol-based dependency injection
- **AI**: Gemini 2.5 Flash (summarization, novel generation), Faster Whisper (transcription), Diffusers (image generation)
- **Database**: Supabase (PostgreSQL) with REST API sync
- **Frontend**: Next.js 16 + React 19 (in `frontend/reader/`)
- **Orchestration**: systemd timers (daily at 03:00 JST) + Task runner

## Architecture: Layered Design

### Domain Layer (`src/domain/`)
Defines interfaces as Protocols (structural subtyping):
- `TranscriberProtocol`: Takes audio → returns transcript + path
- `SummarizerProtocol`: Takes transcript + session → returns summary
- `NovelizerProtocol`: Takes today's summary + prior chapters → returns new chapter
- `ImageGeneratorProtocol`: Takes chapter text → generates PNG
- `StorageProtocol`: Syncs local data to Supabase
- `FileRepositoryProtocol`: File I/O (read, write, archive)

Entities: `RecordingSession` (dataclass with file_paths, start_time, end_time)

### Infrastructure Layer (`src/infrastructure/`)
Concrete implementations:
- **`ai.py`**: Gemini/Whisper/Diffusers clients (Summarizer, Novelizer, ImageGenerator, Curator)
- **`system.py`**: Process monitoring, audio recording, VRChat launch detection
- **`repositories.py`**: FileRepository, TaskRepository (local JSON), SupabaseRepository (cloud sync)
- **`settings.py`**: Pydantic BaseSettings from `data/config.yaml` + environment variables
- **`observability.py`**: TraceLogger logs to `data/traces.jsonl` for debugging

### Use Cases Layer (`src/use_cases/`)
Business logic orchestrators:
- **`ProcessRecordingUseCase`**: Main workflow
  - Inject dependencies via constructor (Transcriber, Summarizer, Novelizer, etc.)
  - `execute(audio_path, sync=True)`: transcribe → summarize → generate novel/image → optionally sync
  - Automatically merges multiple daily audio files into one summary
- **`BuildNovelUseCase`**: Generates chapter from daily summary
- **`EvaluateUseCase`**: Curator grades novel quality

### Entry Points
- **`cli.py` + `cli_handlers.py`**: CLI interface; handlers import use cases and wire dependencies
- **`main.py`**: Dev server (not used in production)
- **Taskfile.yaml**: All operations (see Common Commands below)

## Critical Design Patterns

### Protocol-Based Injection
All use cases depend on `Protocol` interfaces, not concrete classes. This enables:
- Easy mocking for tests
- Swapping implementations (e.g., different transcriber, different LLM)
- Zero coupling to infrastructure

Example:
```python
class ProcessRecordingUseCase:
    def __init__(
        self,
        transcriber: TranscriberProtocol,  # Protocol, not class
        summarizer: SummarizerProtocol,
        ...
    ):
```

### Configuration Management
- **`data/config.yaml`**: Defines audio params, model sizes, paths, image gen settings
- **`src/infrastructure/settings.py`**: Pydantic dataclass loads from YAML + `.env`
- Prompts stored in `settings.prompts` (loaded from YAML)
- Access via `settings.recording_dir`, `settings.gemini_api_key`, etc.

### File Organization
- **`data/recordings/`**: Raw FLAC/WAV (named YYYYMMDD_HHMMSS.flac)
- **`data/transcripts/`**: Raw transcripts + cleaned versions (cleaned_YYYYMMDD_*.txt)
- **`data/summaries/`**: Daily diaries (YYYYMMDD_summary.txt)
- **`data/novels/`**: Long-form chapters (YYYYMMDD.md)
- **`data/photos/`**: Generated illustrations (YYYYMMDD.png) + prompts (YYYYMMDD.txt)
- **`data/evaluations/`**: JSON quality scores per day

## Data Flow

```
VRChat Running
    ↓ (system.py monitors)
→ Audio recorded (sounddevice) → FLAC in data/recordings/
    ↓
process command / daily timer
    ↓
1. Transcribe (Whisper) → data/transcripts/
    ↓
2. Summarize (Gemini) → data/summaries/YYYYMMDD_summary.txt
    ↓
3. Generate Novel (Gemini) → data/novels/YYYYMMDD.md
    ↓
4. Generate Image (Diffusers) → data/photos/YYYYMMDD.png
    ↓
5. Sync to Supabase (SupabaseRepository)
    ├── summaries → daily_entries table
    ├── novels → novels table
    ├── photos → Supabase Storage + URL to DB
    └── evaluations → evaluations table
    ↓
Frontend reads from Supabase
```

## Common Commands

All commands are in `Taskfile.yaml`. Run with `task <command>`.

### Development
```bash
task dev              # Run app (starts recorder/monitor)
task lint             # Format + check with ruff
task setup            # uv sync dependencies
```

### Processing
```bash
task process FILE=data/recordings/20260318_100000.flac     # Single file
task process:today                                          # Today's recordings
task process:yesterday                                      # Yesterday's recordings
task process:daily                                          # Yesterday + today (used by systemd timer)
task process:all                                            # All recordings in directory
task transcribe --file=...                                  # Transcription only
task summarize --file=... or --date=20260318               # Summary only
task novel:build [date=20260318]                           # Novel generation only
```

### Cloud Sync
```bash
task sync              # Sync to Supabase (summaries, novels, photos, evals)
task sync:full         # Force re-sync all files
```

### Web Frontend
```bash
task web:dev           # Start Next.js dev server (port 3000)
task web:build         # Production build
task web:start         # Run prod build (port 4000)
task web:deploy        # Deploy to Vercel
```

### System Status
```bash
task status            # Service + log status
task up                # Enable systemd timer + service
task down              # Disable systemd timer + service
task restart           # Restart service
task logs              # Tail journalctl in real-time
task health:check      # Quick health report (timer active? last run? Supabase up?)
task monitor:daily     # Detailed logs + timer status + journalctl
```

### Maintenance
```bash
task maintenance       # Lint + test + doc checks
task log:clear         # Clear /tmp/vlog-daily.log (weekly)
```

### Management
```bash
task jules add "Buy groceries"              # Add task
task jules list                             # List pending tasks
task jules done <task-id>                   # Mark task complete
task curator eval --date=20260318           # Grade novel quality
task notify --message "Custom message"      # Send Discord notification
```

## Key Files to Know

| File | Purpose |
|------|---------|
| `src/cli_handlers.py` | Parses CLI args, wires dependencies, calls use cases |
| `src/use_cases/*.py` | Business logic (transcribe → summarize → novel → image) |
| `src/infrastructure/ai.py` | Gemini/Whisper/Diffusers clients + prompt templates |
| `src/infrastructure/system.py` | Process monitoring, audio recording |
| `src/infrastructure/repositories.py` | File I/O, task tracking, Supabase sync |
| `data/config.yaml` | All tunable params (model, audio, image, paths, prompts) |
| `data/tasks.json` | Jules task list (JSON) |
| `data/traces.jsonl` | API call logs for debugging |
| `Taskfile.yaml` | All commands + systemd service definitions |
| `docs/MAINTENANCE.md` | systemd timer, Supabase pause handling, recovery steps |
| `docs/DAILY_MONITORING.md` | How to monitor daily runs and troubleshoot |

## Critical Dependencies

### Pydantic Models
The codebase uses Pydantic for all data validation:
- Settings loaded from YAML validated against schema
- RecordingSession is a frozen dataclass (immutable)
- API responses validated before use

### Zero-Try-Except Philosophy
Per project rules, business logic crashes on error rather than catching exceptions. Errors propagate to CLI for visibility. Only systemd+Taskfile error handling exists.

## Important Configuration Notes

### Supabase Free Tier Auto-Pause
- Pauses after 7 days inactivity
- Symptoms: `Could not find table` error during sync
- Recovery: https://supabase.com/dashboard → KafLog project → Resume
- Taskfile now tolerates sync failure (continues with `|| true`)

### systemd Timer (Daily Automation)
- Runs at **03:00 JST** (`OnCalendar=*-*-* 03:00:00`)
- Executes `/snap/bin/task process:daily`
- Logs to systemd journal + `/tmp/vlog-daily.log`
- See `docs/DAILY_MONITORING.md` for troubleshooting

### Model Selection
- **Transcription**: Faster Whisper large-v3-turbo (int8 for speed)
- **Summarization**: Gemini 2.5 Flash
- **Novel generation**: Gemini 2.5 Flash (same model, different prompt)
- **Image generation**: Tongyi-MAI/Z-Image-Turbo (HF diffusers pipeline)

### Whisper Configuration
Located in `data/config.yaml`:
- `language: ja` (Japanese)
- `vad_filter: true` (skip silence)
- `beam_size: 5` (accuracy vs speed)
- `repetition_penalty: 1.08` (reduce hallucination)

## Testing & Debugging

### Run Single Process
```bash
task process FILE=data/recordings/test.flac
```

### Check Latest Traces
```bash
tail -20 data/traces.jsonl  # See API calls, timing, tokens used
```

### Inspect Transcripts
```bash
ls -ltr data/transcripts/ | tail -5
cat data/transcripts/cleaned_20260318_*.txt
```

### Debug Supabase Sync
```bash
task sync  # If fails with "Could not find table", Supabase is paused
```

### Manual Novel Generation (for testing)
```bash
# Read today's summary, generate chapter
task novel:build date=20260318

# Or check if it exists
cat data/novels/20260318.md
```

## Common Modifications

### Change Summarization Prompt
1. Edit `data/config.yaml` → `prompts.summarizer.template`
2. Use variables: `{date}`, `{start_time}`, `{end_time}`, `{transcript}`

### Change Novel Generation Prompt
1. Edit `data/config.yaml` → `prompts.novelizer.template`
2. Use variables: `{novel_so_far}`, `{today_summary}`

### Adjust Image Generation
1. Edit `data/config.yaml` → `image.*` settings (width, height, num_inference_steps, etc.)
2. Change model via `image.model` (must be Diffusers-compatible)

### Add New CLI Command
1. Add subparser in `src/cli.py`
2. Implement handler in `src/cli_handlers.py`
3. Wire dependencies in handler, call use case
4. Add task to `Taskfile.yaml` if needed for daily execution

## Rules & Conventions

- **No try-except in business logic**: Errors crash loudly for visibility
- **Immutability**: Data flows through pipeline without mutation
- **Configuration externalized**: All magic numbers in `data/config.yaml`
- **Prompts externalized**: All LLM prompts in config, never hardcoded
- **Protocols over classes**: Dependencies are Protocols for testability
- **Type hints everywhere**: All functions fully typed
- **FLAC not MP3**: Audio always lossless for transcription quality
- **Dates as YYYYMMDD**: Filenames use fixed format for sorting
