@echo off
call "%~dp0infra\windows\bootstrap.bat" %*
exit /b %ERRORLEVEL%
