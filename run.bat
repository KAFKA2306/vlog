@echo off
pushd "%~dp0"
call "infra\windows\run.bat" %*
popd
exit /b %ERRORLEVEL%
