param(
    [Parameter(Mandatory = $true)]
    [string]$RunScript
)

$runScript = (Resolve-Path -LiteralPath $RunScript).Path
$arguments = '/d /c call ""{0}""' -f $runScript
$action = New-ScheduledTaskAction -Execute $env:ComSpec -Argument $arguments
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Seconds 0) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal
Register-ScheduledTask -TaskName "VlogAutoDiary" -InputObject $task -Force
