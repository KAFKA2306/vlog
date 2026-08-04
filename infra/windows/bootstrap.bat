@echo off
pushd "%~dp0..\.."

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
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0register_task.ps1" -RunScript "%~dp0run.bat" || exit /b %ERRORLEVEL%

echo Bootstrap complete. Task scheduled.
schtasks /Run /TN "VlogAutoDiary"
pause
