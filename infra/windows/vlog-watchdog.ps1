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
$env:XDG_RUNTIME_DIR = "/run/user/1000"
$env:DBUS_SESSION_BUS_ADDRESS = "unix:path=/run/user/1000/bus"

function Write-WatchdogLog([string]$Message) {
    $line = "{0:o} {1}" -f (Get-Date), $Message
    Add-Content -Path $logPath -Value $line -Encoding UTF8
}

$escapedProject = $ProjectPath.Replace("'", "'\''")

try {
    $active = (& wsl.exe -d $Distro -- systemctl --user is-active vlog.service 2>$null | Out-String).Trim()
    $heartbeatPath = "$ProjectPath/data/heartbeats/vlog-service.json"
    $modifiedText = (& wsl.exe -d $Distro -- stat -c %Y $heartbeatPath 2>$null | Out-String).Trim()
    $modified = 0L
    if (-not [int64]::TryParse($modifiedText, [ref]$modified)) {
        $modified = 0L
    }
    $age = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() - $modified
    if ($age -lt 0) {
        $age = 0
    }

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
