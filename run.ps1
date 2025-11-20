Write-Host "Starting VRChat Auto-Diary..." -ForegroundColor Green
$env:UV_PROJECT_ENVIRONMENT = ".venv-win"
uv run python -m src.main
Read-Host -Prompt "Press Enter to exit"
