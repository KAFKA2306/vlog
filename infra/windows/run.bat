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
set "PYTHONIOENCODING=utf-8"
set "PYTHONPATH=%CD%\apps\capture-vrchat;%CD%\packages\memory-domain\src;%CD%\packages\ingestion\src"

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
