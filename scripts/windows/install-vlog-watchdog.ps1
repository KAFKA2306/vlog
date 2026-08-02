param(
    [string]$Distro = "Ubuntu-22.04",
    [string]$ProjectPath = "/home/kafka/projects/vlog"
)

$ErrorActionPreference = "Stop"
$scriptPath = Join-Path $PSScriptRoot "vlog-watchdog.ps1"
if (-not (Test-Path $scriptPath)) {
    throw "Watchdog script not found: $scriptPath"
}

$actionArgs = @{
    Execute = "powershell.exe"
    Argument = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$scriptPath`" -Distro `"$Distro`" -ProjectPath `"$ProjectPath`""
}
$action = New-ScheduledTaskAction @actionArgs

$triggerArgs = @{
    Once = $true
    At = (Get-Date).AddMinutes(1)
    RepetitionInterval = (New-TimeSpan -Minutes 5)
}
$trigger = New-ScheduledTaskTrigger @triggerArgs

$settingsArgs = @{
    AllowStartIfOnBatteries = $true
    DontStopIfGoingOnBatteries = $true
    StartWhenAvailable = $true
    MultipleInstances = "IgnoreNew"
    ExecutionTimeLimit = (New-TimeSpan -Minutes 3)
}
$settings = New-ScheduledTaskSettingsSet @settingsArgs
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

$taskArgs = @{
    TaskName = "VLog External Watchdog"
    Description = "Checks WSL systemd and VLog heartbeat every five minutes and restarts the service when stale."
    Action = $action
    Trigger = $trigger
    Settings = $settings
    Principal = $principal
    Force = $true
}
Register-ScheduledTask @taskArgs | Out-Null

Write-Host "Installed scheduled task: VLog External Watchdog"
Write-Host "Watchdog script: $scriptPath"
