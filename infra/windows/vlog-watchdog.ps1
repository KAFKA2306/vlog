param(
    [string]$Distro = "Ubuntu-22.04",
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,
    [string]$StatePath = $env:VLOG_WSL_STATE_HOME,
    [int]$HeartbeatMaxAgeSeconds = 180
)

$ErrorActionPreference = "Stop"
$windowsState = if ([string]::IsNullOrWhiteSpace($env:VLOG_STATE_HOME)) {
    Join-Path $env:LOCALAPPDATA "VLog\State"
}
else {
    $env:VLOG_STATE_HOME
}
$logDir = Join-Path $windowsState "logs"
$logPath = Join-Path $logDir "watchdog.log"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$env:XDG_RUNTIME_DIR = "/run/user/1000"
$env:DBUS_SESSION_BUS_ADDRESS = "unix:path=/run/user/1000/bus"

function Write-WatchdogLog([string]$Message) {
    $line = "{0:o} {1}" -f (Get-Date), $Message
    Add-Content -Path $logPath -Value $line -Encoding UTF8
}

if (-not $ProjectPath.StartsWith("/")) {
    throw "ProjectPath must be the Linux-native absolute path of the WSL checkout: $ProjectPath"
}
if ($ProjectPath -match '^/mnt/[A-Za-z](?:/|$)') {
    throw "ProjectPath must not use a Windows-mounted /mnt/<drive> code checkout: $ProjectPath"
}
if (-not [string]::IsNullOrWhiteSpace($StatePath) -and -not $StatePath.StartsWith("/")) {
    throw "StatePath must be an absolute POSIX path inside WSL: $StatePath"
}

# Escape a single quote for a Bash single-quoted literal: ' -> '\''
$escapedProject = $ProjectPath.Replace("'", "'\''")
$stateResolver = if ([string]::IsNullOrWhiteSpace($StatePath)) {
    "cd '$escapedProject' && uv run --frozen python -c 'from vlog_capture.portability import runtime_directories; print(runtime_directories().state)'"
}
else {
    $escapedState = $StatePath.Replace("'", "'\''")
    "printf '%s' '$escapedState'"
}

$probe = @"
set -u
PROJECT='$escapedProject'
STATE="`$($stateResolver)"
HEARTBEAT="`$STATE/heartbeats/vlog-service.json"
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
uv run --frozen vlog-operations emit \
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
