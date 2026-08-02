@echo off
set "PROJECT_ROOT=%~dp0.."
pushd "%PROJECT_ROOT%"

set "UV_PROJECT_ENVIRONMENT=.venv-win"
set "UV_LINK_MODE=copy"
set "UV_PYTHON=3.12"
set "PYTHONIOENCODING=utf-8"

set "NVIDIA_BIN=%CD%\.venv-win\Lib\site-packages\nvidia"
set "CUDNN_BIN=%NVIDIA_BIN%\cudnn\bin"
set "CUBLAS_BIN=%NVIDIA_BIN%\cublas\bin"
set "PATH=%CUDNN_BIN%;%CUBLAS_BIN%;%PATH%"

if not exist "data\logs" mkdir "data\logs"
set "BOOTSTRAP_LOG=data\logs\windows-bootstrap.log"
> "%BOOTSTRAP_LOG%" echo timestamp=%DATE% %TIME%
>> "%BOOTSTRAP_LOG%" echo resolved_path=%CD%
>> "%BOOTSTRAP_LOG%" echo working_dir=%CD%

uv run --frozen python -m src.main >> "%BOOTSTRAP_LOG%" 2>&1
set "EXIT_CODE=%ERRORLEVEL%"
>> "%BOOTSTRAP_LOG%" echo exit_code=%EXIT_CODE%
popd
exit /b %EXIT_CODE%
