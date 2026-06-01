@echo off
pushd "%~dp0.."

set "UV_PROJECT_ENVIRONMENT=.venv-win"
set "UV_LINK_MODE=copy"
set "UV_PYTHON=3.12"
set "PYTHONIOENCODING=utf-8"

for /f "delims=" %%i in ('uv run python -c "import nvidia.cudnn; import os; print(os.path.join(os.path.dirname(nvidia.cudnn.__file__), 'bin'))" 2^>nul') do set "CUDNN_BIN=%%i"
if defined CUDNN_BIN set "PATH=%CUDNN_BIN%;%PATH%"

uv run python -m src.main
pause
