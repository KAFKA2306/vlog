param(
    [string]$Distro = "Ubuntu-22.04",
    [string]$ProjectPath = ""
)

$ErrorActionPreference = "Stop"
$scriptPath = Join-Path $PSScriptRoot "vlog-watchdog.ps1"
if (-not (Test-Path $scriptPath)) {
    throw "Watchdog script not found: $scriptPath"
}

if ([string]::IsNullOrWhiteSpace($ProjectPath)) {
    $windowsRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
    $ProjectPath = (& wsl.exe -d $Distro -- wslpath -a $windowsRoot | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($ProjectPath)) {
        throw "Could not derive the WSL project path from: $windowsRoot"
    }
}

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$scriptPath`" -Distro `"$Distro`" -ProjectPath `"$ProjectPath`""
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
    -Description "Checks WSL systemd and VLog heartbeat every five minutes and restarts the service when stale." `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Force | Out-Null

Write-Host "Installed scheduled task: VLog External Watchdog"
Write-Host "Watchdog script: $scriptPath"
Write-Host "WSL project path: $ProjectPath"
