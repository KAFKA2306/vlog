@echo off
pushd "%~dp0.."

set "UV_PROJECT_ENVIRONMENT=.venv-win"
set "UV_LINK_MODE=copy"
set "UV_PYTHON=3.12"

if exist ".env.example" (
  if not exist ".env" (
    copy ".env.example" ".env"
  )
)

if not exist ".env" (
  type nul > ".env"
)





if not exist "data\recordings" mkdir "data\recordings"
if not exist "data\transcripts" mkdir "data\transcripts"
if not exist "data\summaries" mkdir "data\summaries"
if not exist "data\archives" mkdir "data\archives"
if not exist "data\logs" mkdir "data\logs"
uv sync --frozen || exit /b %ERRORLEVEL%
schtasks /Create /TN "VlogAutoDiary" /TR "\"%~dp0run.bat\"" /SC ONLOGON /RL HIGHEST /F /DELAY 0000:30 /RU "%USERNAME%"
powershell.exe -NoProfile -Command "$task = Get-ScheduledTask -TaskName 'VlogAutoDiary'; $task.Settings.RestartCount = 999; $task.Settings.RestartInterval = 'PT1M'; $task.Settings.ExecutionTimeLimit = 'PT0S'; $task.Settings.DisallowStartIfOnBatteries = $false; $task.Settings.StopIfGoingOnBatteries = $false; Set-ScheduledTask -InputObject $task"

echo Bootstrap complete. Task scheduled.
schtasks /Run /TN "VlogAutoDiary"
pause
