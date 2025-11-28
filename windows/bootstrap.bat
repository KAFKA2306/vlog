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

set "RECORDING_PATH=%CD%\data\recordings"
set "TRANSCRIPT_PATH=%CD%\data\transcripts"

findstr /C:"VLOG_RECORDING_DIR=" .env >nul 2>&1
if errorlevel 1 (
  echo VLOG_RECORDING_DIR=%RECORDING_PATH%>> .env
)

findstr /C:"VLOG_TRANSCRIPT_DIR=" .env >nul 2>&1
if errorlevel 1 (
  echo VLOG_TRANSCRIPT_DIR=%TRANSCRIPT_PATH%>> .env
)

if not exist "data" mkdir "data"
if not exist "data\recordings" mkdir "data\recordings"
if not exist "data\transcripts" mkdir "data\transcripts"
if not exist "data\summaries" mkdir "data\summaries"
if not exist "data\archives" mkdir "data\archives"
if not exist "logs" mkdir "logs"

schtasks /Create /TN "VlogAutoDiary" /TR "\"%~dp0run.bat\"" /SC ONLOGON /RL HIGHEST /F /DELAY 0000:30 /RU "%USERNAME%"

echo Bootstrap complete. Task scheduled.
start /min "" "%~dp0run.bat"
pause
