$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$env:UV_PROJECT_ENVIRONMENT = ".venv-win"
$env:UV_LINK_MODE = "copy"
Write-Host "Starting VRChat Auto-Diary..." -ForegroundColor Green
uv run python -m src.main
Read-Host -Prompt "Press Enter to exit"
