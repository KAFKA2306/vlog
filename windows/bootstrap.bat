@echo off
pushd "%~dp0.."

set "UV_PROJECT_ENVIRONMENT=.venv-win"
set "UV_LINK_MODE=copy"

REM Detect Microsoft Store Python aliases that cannot be copied into virtualenvs.
for /f "delims=" %%P in ('where python 2^>nul') do (
  set "PYTHON_PATH=%%~fP"
  goto :got_python
)
:got_python
if defined PYTHON_PATH (
  echo Detected Python at "%PYTHON_PATH%".
  echo.
  echo Microsoft Store/alias Python cannot be used to build virtual environments under some installers.
  echo Please install the official Python 3.11+ distribution from https://www.python.org/downloads/windows
  echo and place its directory earlier in your PATH, then re-run this script.
  echo.
  echo Bootstrap aborted.
  pause
  exit /b 1
)

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
