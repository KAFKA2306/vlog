---
name: media-expert
description: Operating guide for audio processing, image generation, and media quality control in VLog. Trigger this skill whenever users mention audio format/resampling, VAD behavior, Opus transcoding, image output specs, or media integrity checks.
---

# Media Expert Skill

## 1. Audio Pipeline
- Format standards must follow `src/infrastructure/settings.py`.
- Capture: hardware-native input (`48kHz`, stereo).
- Processing target: AI-normalized (`16kHz`, mono).
- VAD: use `webrtcvad` with a pre-roll buffer to prevent clipped speech starts.

## 2. Persistence and Integrity
- Primary persistence is local filesystem.
- Supabase is a synchronization target, not the primary source of truth.
- Directory expectations:
  - `data/recordings/` for raw/compressed audio
  - `data/transcripts/` for transcription outputs
  - `data/summaries/` for summary outputs
  - `data/novels/` for narrative outputs
- Verify generated outputs remain consistent with source logs.

## 3. Image Generation
- Output specs: `1024x1024`, `.png` quality 90.
- Link generated images to the relevant date/event in the Supabase database.

## 4. Failure Policy
- If core media steps fail (model/DB), stop and surface the failure immediately.
- Require structured logs for conversion, recognition, and persistence steps.
