# Repository Guidelines

Documents must be written by Japanese.
Response in Japanese to User.

create and update README.md in all directories in Japanese

## Project Structure & Module Organization

The project is source-first: `src/main.py` launches `Application`, which orchestrates the process monitor and recorder. Long-running orchestration lives in `src/app.py`; reusable infrastructure (settings, audio capture, Whisper-based transcription, summarization, process monitoring) sits in `src/infrastructure/`. Domain DTOs live in `src/domain/`, while executable workflows reside under `src/services/recorder_service.py` and `src/services/processor_service.py`. Runtime artifacts such as `recordings/` and `diaries/` are created alongside the repo root and should be kept out of version control thanks to `.gitignore`. Add future tests under a top-level `tests/` package mirroring `src/`.

## Build, Test, and Development Commands

- `uv sync` – recreate the `.venv` using `pyproject.toml` + `uv.lock`; run whenever dependencies change.
- `uv run python -m src.main` – start the monitoring loop; runs indefinitely until interrupted.
- `uv run ruff check . --fix` – lint with Ruff (line length 88) and auto-fix imports/pep8 violations.
- `uv run ruff format` – apply Ruff’s formatter to enforce consistent style.
- `uv run pytest` – reserved for the upcoming test suite; prefer the `-q` flag for CI friendliness once tests exist.

## Coding Style & Naming Conventions

Code targets Python 3.11 with type hints and dataclasses where helpful (`src/domain/entities.py`). Keep lines ≤88 chars (see `[tool.ruff]`), use four-space indentation, snake_case filenames, and noun-based class names. Public functions should describe their action (`get_latest_recording`), and long-running workflows deserve short docstrings or inline comments explaining sequencing. When touching settings, expose configurable values via `Settings` in `src/infrastructure/settings.py` instead of hardcoding elsewhere.

## Testing Guidelines

Automated tests are not yet implemented; new contributions must add pytest-based coverage alongside features. Mirror the `src/` tree (`tests/infrastructure/test_audio_recorder.py`, etc.), use descriptive test names (`test_<behavior>_<context>`), and include regression fixtures for audio/transcription edge cases. Aim for at least smoke tests covering recorder start/stop logic, transcription fallbacks, and processor diary writes. Run `uv run pytest` locally before opening a PR and capture any added assets under `tests/fixtures/`.

## Commit & Pull Request Guidelines

Commits follow short, imperative messages (`Add initial vlog app files`, `Add Python gitignore`). Keep scope focused, reference issues in the body when available, and avoid bundling unrelated formatting with feature work. PRs should include: summary of changes, manual/automated test evidence (`uv run ruff check`, `uv run pytest` output), configuration notes (e.g., new settings), and screenshots or diary samples if user-facing behavior changed. Request reviewers only after lint/tests pass and large assets are excluded from git history.
