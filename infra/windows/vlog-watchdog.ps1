param(
    [string]$Distro = "Ubuntu-22.04",
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,
    [int]$HeartbeatMaxAgeSeconds = 180
)

$ErrorActionPreference = "Stop"
$logDir = Join-Path $env:LOCALAPPDATA "VLog"
$logPath = Join-Path $logDir "watchdog.log"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Write-WatchdogLog([string]$Message) {
    $line = "{0:o} {1}" -f (Get-Date), $Message
    Add-Content -Path $logPath -Value $line -Encoding UTF8
}

$escapedProject = $ProjectPath.Replace("'", "'\"'\"'")
$probe = @"
set -u
PROJECT='$escapedProject'
HEARTBEAT="`$PROJECT/data/heartbeats/vlog-service.json"
active="`$(systemctl --user is-active vlog.service 2>/dev/null || true)"
if [[ -f "`$HEARTBEAT" ]]; then
  now="`$(date +%s)"
  modified="`$(stat -c %Y "`$HEARTBEAT" 2>/dev/null || echo 0)"
  age="`$((now - modified))"
else
  age=999999
fi
printf '%s %s\n' "`$active" "`$age"
"@

try {
    $result = (& wsl.exe -d $Distro -- bash -lc $probe 2>&1 | Out-String).Trim()
    $parts = $result -split '\s+'
    $active = if ($parts.Count -ge 1) { $parts[0] } else { "unknown" }
    $age = if ($parts.Count -ge 2 -and $parts[1] -match '^\d+$') { [int]$parts[1] } else { 999999 }

    if ($active -eq "active" -and $age -le $HeartbeatMaxAgeSeconds) {
        Write-WatchdogLog "healthy service=$active heartbeat_age=${age}s"
        exit 0
    }

    Write-WatchdogLog "unhealthy service=$active heartbeat_age=${age}s; restarting"
    $repair = @"
set -euo pipefail
cd '$escapedProject'
systemctl --user reset-failed vlog.service || true
systemctl --user restart vlog.service
PYTHONPATH=apps/capture-vrchat:packages/memory-domain/src:packages/ingestion/src uv run python -m src.operations emit \
  --category infrastructure \
  --component windows-watchdog \
  --operation external_probe \
  --status recovered \
  --severity warning \
  --code windows_watchdog_restart \
  --resource-id vlog.service \
  --message 'Windows watchdog restarted stale or inactive vlog.service'
"@
    & wsl.exe -d $Distro -- bash -lc $repair | Out-Null
    Write-WatchdogLog "restart requested successfully"
    exit 0
}
catch {
    Write-WatchdogLog "watchdog error: $($_.Exception.Message)"
    exit 1
}
