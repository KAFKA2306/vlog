@echo off
setlocal
set "PROJECT_ROOT=%~dp0..\.."

if "%PROJECT_ROOT:~0,2%"=="\\" (
  echo ERROR: VLog production Windows checkout must be on a Windows-native drive, not UNC or a WSL share: "%PROJECT_ROOT%" 1>&2
  exit /b 1
)

pushd "%PROJECT_ROOT%" 2>nul
if errorlevel 1 (
  echo ERROR: Could not open the project directory: "%PROJECT_ROOT%" 1>&2
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
set "PYTHONIOENCODING=utf-8"

if not defined VLOG_UV_EXE (
  for /f "delims=" %%I in ('where uv.exe 2^>nul') do if not defined VLOG_UV_EXE set "VLOG_UV_EXE=%%I"
)
if not defined VLOG_UV_EXE (
  echo ERROR: uv.exe could not be resolved. Re-run bootstrap/register_task.ps1. 1>&2
  popd
  exit /b 1
)
if not exist "%VLOG_UV_EXE%" (
  echo ERROR: Resolved uv.exe does not exist: "%VLOG_UV_EXE%" 1>&2
  popd
  exit /b 1
)

for /f "usebackq delims=" %%I in (`"%VLOG_UV_EXE%" run --frozen python -c "import pathlib,nvidia.cudnn; print(pathlib.Path(nvidia.cudnn.__file__).parent/'bin')"`) do set "CUDNN_BIN=%%I"
for /f "usebackq delims=" %%I in (`"%VLOG_UV_EXE%" run --frozen python -c "import pathlib,nvidia.cublas; print(pathlib.Path(nvidia.cublas.__file__).parent/'bin')"`) do set "CUBLAS_BIN=%%I"
if defined CUDNN_BIN set "PATH=%CUDNN_BIN%;%PATH%"
if defined CUBLAS_BIN set "PATH=%CUBLAS_BIN%;%PATH%"

if not exist "%VLOG_CONFIG_HOME%" mkdir "%VLOG_CONFIG_HOME%"
if not exist "%VLOG_DATA_HOME%" mkdir "%VLOG_DATA_HOME%"
if not exist "%VLOG_STATE_HOME%\logs" mkdir "%VLOG_STATE_HOME%\logs"
if not exist "%VLOG_CACHE_HOME%" mkdir "%VLOG_CACHE_HOME%"
set "BOOTSTRAP_LOG=%VLOG_STATE_HOME%\logs\windows-bootstrap.log"
> "%BOOTSTRAP_LOG%" echo timestamp=%DATE% %TIME%
>> "%BOOTSTRAP_LOG%" echo resolved_path=%CD%
>> "%BOOTSTRAP_LOG%" echo working_dir=%CD%
>> "%BOOTSTRAP_LOG%" echo uv_executable=%VLOG_UV_EXE%
>> "%BOOTSTRAP_LOG%" echo data_home=%VLOG_DATA_HOME%
>> "%BOOTSTRAP_LOG%" echo state_home=%VLOG_STATE_HOME%

"%VLOG_UV_EXE%" run --frozen vlog-service >> "%BOOTSTRAP_LOG%" 2>&1
set "EXIT_CODE=%ERRORLEVEL%"
>> "%BOOTSTRAP_LOG%" echo exit_code=%EXIT_CODE%
popd
exit /b %EXIT_CODE%
