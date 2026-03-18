# VLog systemd & Supabase Maintenance (2026-03-18)

## Critical Issue: Supabase Free Tier Auto-Pause
**Status**: PAUSED as of 2026-03-18
**Next pause deadline**: 2026-05-31 (unless manually resumed)

### Root Cause
When Supabase pauses:
1. `task process:daily` runs normally (transcription, summarization, novel generation all work)
2. `task sync` step fails with: `postgrest.exceptions.APIError: Could not find the table 'public.evaluations'`
3. Task exits with code 201
4. Systemd misinterprets as `status=201/NICE` (though not actually a permission error)

### Fix Applied (2026-03-18)
- **Taskfile.yaml**: Changed `task sync` to `task sync || echo "warning"` so sync failure doesn't block `process:daily`
- **systemd service**: Already correct (`/snap/bin/task process:daily`)
- **Cleanup**: Deleted unused directories (`novels\ copy/`, `mbti_analysis/`, `logs/`)
- **Docs**: Created `docs/MAINTENANCE.md` with recovery procedures

### Supabase Resume Procedure
```
https://supabase.com/dashboard → KafLog project → "Resume project" button
```
Takes 2-3 minutes. After resume, run `task sync` to restore evaluations table.

### Why This Happens
- Free tier Supabase suspends after 7 days with zero database activity
- Last successful processing was 2026-03-17 08:34
- Auto-resume would require checking Supabase API status, not yet implemented

## Systemd Configuration
- **Timer**: 03:00 JST daily (OnCalendar=*-*-* 03:00:00)
- **Service**: Executes /snap/bin/task process:daily
- **Status**: Working correctly; exit 201 is from task (not NICE error)
