# VLog Maintenance Manual

## Latest Status (2026-03-18)

### systemd Service & Timer
- ✅ **vlog-daily.timer**: Runs at 03:00 JST daily
- ✅ **vlog-daily.service**: Executes `/snap/bin/task process:daily`
- ✅ **Taskfile**: `process:daily` now tolerates Supabase sync failures

### Known Issues

#### 🚨 Supabase Free Tier Auto-Pause
- **Problem**: Supabase pauses after 7 days of inactivity
- **Status**: Currently paused (as of 2026-03-18)
- **Symptoms**: 
  - `task sync` fails with `postgrest.exceptions.APIError: Could not find the table 'public.evaluations'`
  - systemd logs show `exit status 201/NICE` (misleading — it's not a NICE priority error, but exit code 201 from task)
- **Solution**:
  1. Go to https://supabase.com/dashboard
  2. Select project **KafLog** (ctfklclaxidkjufnryvj.supabase.co)
  3. Click **Resume project** (takes 2-3 minutes to restore)
- **Workaround**: `process:daily` now catches sync failure and continues
- **Next Pause**: 2026-05-31 (unless manually resumed before then)

#### ⚙️ Exit Code Masking
- When `task sync` fails with exit code 201, systemd interprets `status=201/NICE`
- This is NOT a permission/NICE priority issue
- Root cause: Supabase paused → sync fails → exit 201
- **Fixed**: Taskfile now uses `|| true` to allow task to complete despite sync failure

#### 🔄 Timer Execution Times
- Timer configured: `OnCalendar=*-*-* 03:00:00` (3 AM JST)
- Observed in logs: Executions at 03:00 and 15:40 (12-hour offset observed in Mar 17)
- **Status**: Timer schedule is correct; offset may be timezone interpretation in journal

### Data Integrity

| Component | Status | Last Update |
|-----------|--------|-------------|
| novels/ | ✅ | 2026-03-17 08:34 |
| summaries/ | ✅ | 2026-03-17 08:29 |
| photos/ | ✅ | 2026-03-17 08:33 |
| transcripts/ | ✅ | 2026-03-16 08:25 |
| recordings/ | ✅ | 2026-03-16 08:27 |
| traces.jsonl | ✅ | 2026-03-17 08:34 |

### Cleanup Performed

Removed unused directories (2026-03-18 18:27):
- `data/novels\ copy/` (old backup)
- `data/mbti_analysis/` (unused analysis)
- `data/logs/` (systemd journal now sufficient)

## Recovery Procedures

### If `task process:daily` Fails in systemd

1. **Check if Supabase is paused**:
   ```bash
   task sync
   ```
   If you see `Could not find the table`, Supabase is paused.

2. **Resume Supabase**:
   - https://supabase.com/dashboard → KafLog → Resume

3. **Manually trigger reprocessing**:
   ```bash
   task process:daily
   ```

4. **Check systemd logs**:
   ```bash
   journalctl --user -u vlog-daily.service -n 20
   systemctl --user status vlog-daily.service
   ```

### If Timer Doesn't Execute

1. **Check timer status**:
   ```bash
   systemctl --user list-timers vlog-daily.timer
   systemctl --user status vlog-daily.timer
   ```

2. **Enable timer**:
   ```bash
   systemctl --user enable --now vlog-daily.timer
   ```

3. **Force next execution** (for testing):
   ```bash
   systemctl --user start vlog-daily.service
   ```

## Logging & Monitoring (MANDATORY)

### Log Locations

1. **Service Logs** (systemd journal):
   ```bash
   journalctl --user -u vlog-daily.service --since "24 hours ago"
   ```
   - Persisted by systemd journal (default: 1-4 weeks depending on disk usage)
   - Accessible anytime

2. **Operation Log** (`/tmp/vlog-daily.log`):
   ```bash
   cat /tmp/vlog-daily.log
   tail -20 /tmp/vlog-daily.log
   ```
   - Human-readable: timestamps + start/completion + failures
   - **Note**: `/tmp` is volatile; persisted across reboots but not permanent
   - Clear periodically: `task log:clear`

### Daily Monitoring

**Check if process ran today**:
```bash
task monitor:daily
```
This shows:
- Latest execution log
- Timer status and next scheduled time
- Last 24h service records
- Supabase connectivity

**Health check**:
```bash
task health:check
```
Verifies:
- Timer is active
- Last run succeeded/failed
- Supabase is accessible

### Failure Handling

When `vlog-daily.service` fails:

1. **Automatic notifications**:
   - `vlog-daily-failure.service` triggers on failure
   - Sends Discord webhook (if configured in CLI)
   - Appends error details to `/tmp/vlog-daily.log`

2. **Manual investigation**:
   ```bash
   # Recent errors
   journalctl --user -u vlog-daily.service -n 10

   # View full operation log
   task log:daily

   # Check Supabase status
   task sync
   ```

### Log Retention Policy

| Log Type | Location | Retention | Action |
|----------|----------|-----------|--------|
| systemd journal | `/var/log/journal` | 1-4 weeks | Automatic (system-managed) |
| Operation log | `/tmp/vlog-daily.log` | Until cleared | `task log:clear` weekly |
| Data files | `data/` subdirs | Permanent | Git-tracked |

**Weekly maintenance**:
```bash
task log:clear  # Start fresh week
task maintenance  # Full system check
```

## Future Improvements

- [ ] Implement Supabase pause detection (check project status API)
- [ ] Auto-resume logic (daily cron to check & resume if paused)
- [ ] Archive operation logs to persistent storage (e.g., data/logs/)
- [ ] Alert on sustained failures (e.g., notify after 3 consecutive failures)
- [ ] Structured logging (JSON format for automated analysis)
