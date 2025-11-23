@echo off
setlocal
pushd "%~dp0" >nul 2>&1
if errorlevel 1 (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1"
  exit /b %errorlevel%
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%CD%\\run.ps1"
popd
endlocal
