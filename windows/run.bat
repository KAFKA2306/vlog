@echo off
pushd "%~dp0.."

set "UV_PROJECT_ENVIRONMENT=.venv-win"
set "UV_LINK_MODE=copy"
set "PYTHONIOENCODING=utf-8"



set "HF_ENDPOINT=https://hf-mirror.com"



uv run python -m src.main
pause
