Write-Host "Starting VRChat Auto-Diary..." -ForegroundColor Green
Write-Host "Starting VRChat Auto-Diary..." -ForegroundColor Green
$env:UV_PROJECT_ENVIRONMENT = ".venv-win"
$env:UV_LINK_MODE = "copy"
uv run python -m src.main
Read-Host -Prompt "Press Enter to exit"
