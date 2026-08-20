param(
    [Parameter(Mandatory = $true)]
    [string]$RunScript
)

$ErrorActionPreference = "Stop"

$runScript = (Resolve-Path -LiteralPath $RunScript).ProviderPath
$repoRoot = Split-Path -Parent $runScript
while ($repoRoot -and -not (Test-Path -LiteralPath (Join-Path $repoRoot "pyproject.toml") -PathType Leaf)) {
    $parent = Split-Path -Parent $repoRoot
    if (-not $parent -or $parent -eq $repoRoot) {
        throw "Could not resolve VLog repository root from $runScript"
    }
    $repoRoot = $parent
}

if ($repoRoot.StartsWith("\\")) {
    throw "VLog Task Scheduler requires a Windows-native checkout, not UNC/WSL share: $repoRoot"
}

$cmd = (Get-Command cmd.exe -ErrorAction Stop).Source
$uv = (Get-Command uv.exe -ErrorAction Stop).Source
$arguments = '/d /c "set ""VLOG_UV_EXE={0}"" && call ""{1}"""' -f $uv, $runScript
$action = New-ScheduledTaskAction `
    -Execute $cmd `
    -Argument $arguments `
    -WorkingDirectory $repoRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Days 3) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName "VlogAutoDiary" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "VLog automatic capture" `
    -Force | Out-Null

Write-Host "Registered VlogAutoDiary"
Write-Host "  executable: $cmd"
Write-Host "  uv: $uv"
Write-Host "  working directory: $repoRoot"
Write-Host "  run script: $runScript"
