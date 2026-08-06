@echo off
setlocal
set "PROJECT_ROOT=%~dp0..\.."
pushd "%PROJECT_ROOT%" 2>nul
if errorlevel 1 (
  echo ERROR: Could not open the project directory: "%PROJECT_ROOT%" 1>&2
  echo If the repository is on a UNC or WSL share, map it to a Windows drive or copy it to a local Windows path, then run this script again. 1>&2
  exit /b 1
)

if not exist "pyproject.toml" (
  echo ERROR: The resolved project directory is invalid: "%CD%" 1>&2
  popd
  exit /b 1
)

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
uv sync --frozen
if errorlevel 1 (
  set "EXIT_CODE=%ERRORLEVEL%"
  popd
  exit /b %EXIT_CODE%
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0register_task.ps1" -RunScript "%~dp0run.bat"
if errorlevel 1 (
  set "EXIT_CODE=%ERRORLEVEL%"
  popd
  exit /b %EXIT_CODE%
)

echo Bootstrap complete. Task scheduled.
schtasks /Run /TN "VlogAutoDiary"
set "EXIT_CODE=%ERRORLEVEL%"
popd
pause
exit /b %EXIT_CODE%
