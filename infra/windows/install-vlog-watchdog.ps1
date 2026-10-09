param(
    [string]$Distro = "Ubuntu-22.04",
    [string]$ProjectPath = $env:VLOG_WSL_PROJECT_ROOT,
    [string]$StatePath = $env:VLOG_WSL_STATE_HOME
)

$ErrorActionPreference = "Stop"
$scriptPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "vlog-watchdog.ps1")).ProviderPath

if ([string]::IsNullOrWhiteSpace($ProjectPath)) {
    throw "Set VLOG_WSL_PROJECT_ROOT or pass -ProjectPath with the Linux-native WSL checkout path. Automatic Windows-path-to-WSL-path conversion is intentionally not used."
}
if (-not $ProjectPath.StartsWith("/")) {
    throw "ProjectPath must be an absolute POSIX path inside WSL: $ProjectPath"
}
if ($ProjectPath -match '^/mnt/[A-Za-z](?:/|$)') {
    throw "ProjectPath must be a Linux-native checkout, not /mnt/<drive>: $ProjectPath"
}
if (-not [string]::IsNullOrWhiteSpace($StatePath) -and -not $StatePath.StartsWith("/")) {
    throw "StatePath must be an absolute POSIX path inside WSL: $StatePath"
}

$powershell = (Get-Command powershell.exe -ErrorAction Stop).Source
$arguments = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$scriptPath`" -Distro `"$Distro`" -ProjectPath `"$ProjectPath`""
if (-not [string]::IsNullOrWhiteSpace($StatePath)) {
    $arguments += " -StatePath `"$StatePath`""
}
$action = New-ScheduledTaskAction `
    -Execute $powershell `
    -Argument $arguments `
    -WorkingDirectory (Split-Path -Parent $scriptPath)
$trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes 5)
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 3)
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName "VLog External Watchdog" `
    -Description "Checks the Linux-native WSL VLog systemd service every five minutes and restarts it when stale." `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Force | Out-Null

Write-Host "Installed scheduled task: VLog External Watchdog"
Write-Host "Watchdog script: $scriptPath"
Write-Host "PowerShell: $powershell"
Write-Host "WSL native project path: $ProjectPath"
if (-not [string]::IsNullOrWhiteSpace($StatePath)) {
    Write-Host "WSL runtime state path: $StatePath"
}
else {
    Write-Host "WSL runtime state path: discovered from platformdirs at watchdog runtime"
}
