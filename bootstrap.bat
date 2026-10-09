@echo off
pushd "%~dp0"
call "infra\windows\bootstrap.bat" %*
popd
exit /b %ERRORLEVEL%
