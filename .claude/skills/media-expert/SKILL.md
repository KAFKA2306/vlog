---
name: media-expert
description: Operating guide for audio processing, image generation, and media quality control in VLog. Trigger this skill whenever users mention audio format/resampling, VAD behavior, Opus transcoding, image output specs, or media integrity checks, because these tasks require strict parameter consistency from project constants and are easy to break with ad-hoc changes.
user-invocable: false
allowed-tools:
  - Read
---

# Media Expert Skill

## 1. Audio Pipeline
- Format standards must follow `src/domain/constants.rs`.
- Capture: hardware-native input (`48kHz`, stereo).
- Processing target: AI-normalized (`16kHz`, mono).
- Opus transcoding: output `24kbps VBR`; delete WAV/FLAC only after successful transcode.
- VAD: use `webrtcvad` with a pre-roll buffer to prevent clipped speech starts.

## 2. Persistence and Integrity
- Primary persistence is local filesystem + SQLite.
- Supabase is a synchronization target, not the primary source of truth.
- Directory expectations:
  - `data/recordings/` for raw/compressed audio
  - `data/transcripts/` for transcription outputs
  - `data/summaries/` for summary outputs
- Verify generated outputs remain consistent with source logs.

## 3. Context Enrichment
- Treat silence and inactivity periods as context signals, not missing data.
- Include background media/activity context when producing narrative outputs.

## 4. Image Generation
- Output format: `9:16`, `1024x1792`, `.webp` quality 90.
- Link generated images to the relevant date/event so outputs stay auditable.

## 5. Failure Policy
- If core media steps fail (ffmpeg/model/DB), stop and surface the failure immediately.
- Require structured logs for conversion, recognition, and persistence steps.
