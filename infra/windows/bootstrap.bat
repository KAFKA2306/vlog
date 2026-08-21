@echo off
setlocal
set "PROJECT_ROOT=%~dp0..\.."
pushd "%PROJECT_ROOT%" 2>nul
if errorlevel 1 (
  echo ERROR: Could not open the project directory: "%PROJECT_ROOT%" 1>&2
  echo Use a Windows-native local checkout; UNC and WSL-share code checkouts are not supported for production. 1>&2
  exit /b 1
)

if not exist "pyproject.toml" (
  echo ERROR: The resolved project directory is invalid: "%CD%" 1>&2
  popd
  exit /b 1
)

set "VLOG_PROJECT_ROOT=%CD%"
if not defined VLOG_CONFIG_HOME set "VLOG_CONFIG_HOME=%APPDATA%\VLog"
if not defined VLOG_DATA_HOME set "VLOG_DATA_HOME=%LOCALAPPDATA%\VLog\Data"
if not defined VLOG_STATE_HOME set "VLOG_STATE_HOME=%LOCALAPPDATA%\VLog\State"
if not defined VLOG_CACHE_HOME set "VLOG_CACHE_HOME=%LOCALAPPDATA%\VLog\Cache"
set "UV_PROJECT_ENVIRONMENT=.venv-win"
set "UV_LINK_MODE=copy"
set "UV_PYTHON=3.12"

if not exist "%VLOG_CONFIG_HOME%" mkdir "%VLOG_CONFIG_HOME%"
if not exist "%VLOG_DATA_HOME%" mkdir "%VLOG_DATA_HOME%"
if not exist "%VLOG_STATE_HOME%" mkdir "%VLOG_STATE_HOME%"
if not exist "%VLOG_CACHE_HOME%" mkdir "%VLOG_CACHE_HOME%"

uv sync --locked --extra gpu
if errorlevel 1 goto :failed

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0register_task.ps1" -RunScript "%~dp0run.bat"
if errorlevel 1 goto :failed

echo Bootstrap complete. Runtime state is outside the Git checkout.
echo Config: %VLOG_CONFIG_HOME%
echo Data:   %VLOG_DATA_HOME%
echo State:  %VLOG_STATE_HOME%
echo Cache:  %VLOG_CACHE_HOME%
schtasks /Run /TN "VlogAutoDiary"
if errorlevel 1 goto :failed
popd
pause
exit /b 0

:failed
popd
exit /b 1
