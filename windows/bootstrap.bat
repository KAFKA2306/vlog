@echo off
pushd "%~dp0.."

set "UV_PROJECT_ENVIRONMENT=.venv-win"
set "UV_LINK_MODE=copy"

if exist ".env.example" (
  if not exist ".env" (
    copy ".env.example" ".env"
  )
)

if not exist ".env" (
  type nul > ".env"
)





schtasks /Create /TN "VlogAutoDiary" /TR "\"%~dp0run.bat\"" /SC ONLOGON /RL HIGHEST /F /DELAY 0000:30 /RU "%USERNAME%"

echo Bootstrap complete. Task scheduled.
start /min "" "%~dp0run.bat"
pause
