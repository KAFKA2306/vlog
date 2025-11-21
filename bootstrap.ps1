$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$env:UV_PROJECT_ENVIRONMENT = ".venv-win"
$env:UV_LINK_MODE = "copy"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {python -m pip install --upgrade uv}
if (Test-Path .env.example -and -not (Test-Path .env)) {Copy-Item .env.example .env}
if (-not $env:GOOGLE_API_KEY) {$env:GOOGLE_API_KEY = Read-Host "GOOGLE_API_KEY"}
if (-not (Select-String -Path .env -Pattern '^GOOGLE_API_KEY=' -Quiet)) {"GOOGLE_API_KEY=$($env:GOOGLE_API_KEY)" | Add-Content .env}
uv sync
$vbs = Join-Path $root "run_silent.vbs"
$launcherDir = Join-Path $env:LOCALAPPDATA "VlogAutoDiary"
New-Item -ItemType Directory -Force -Path $launcherDir | Out-Null
$launcher = Join-Path $launcherDir "launch.cmd"
Set-Content -Path $launcher -Value "@echo off`r`npushd `"$root`"`r`nwscript.exe `"$vbs`"`r`n" -Encoding ASCII
schtasks /Create /TN "VlogAutoDiary" /TR "`"$launcher`"" /SC ONLOGON /RL HIGHEST /F /DELAY 0000:30 /RU "$env:USERNAME"
Start-Process -FilePath $launcher
