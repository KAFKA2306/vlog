@echo off
call "%~dp0infra\windows\run.bat" %*
exit /b %ERRORLEVEL%
