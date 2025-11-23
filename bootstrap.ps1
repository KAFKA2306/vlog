$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$envRoot = $root
if ($root -like "\\\\*") {
    $driveLetter = "Z:"
    try {
        cmd /c "net use $driveLetter `"$root`" /persistent:no >nul 2>&1"
        if (Test-Path $driveLetter) { $envRoot = "$driveLetter\" }
    } catch {
        Write-Warning "net use failed; continuing with UNC path. Map this repo to a drive (e.g. Z:) for reliable recording path resolution."
    }
}
Set-Location $envRoot
$env:UV_PROJECT_ENVIRONMENT = ".venv-win"
$env:UV_LINK_MODE = "copy"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    try { python -m pip install --upgrade uv } catch { Write-Warning "uv install failed: $_" }
}
if (Test-Path .env.example -and -not (Test-Path .env)) {Copy-Item .env.example .env}
if (-not (Test-Path .env)) {New-Item -ItemType File -Path .env | Out-Null}
if (-not $env:GOOGLE_API_KEY) {$env:GOOGLE_API_KEY = Read-Host "GOOGLE_API_KEY"}
if (-not (Select-String -Path .env -Pattern '^GOOGLE_API_KEY=' -Quiet -ErrorAction SilentlyContinue)) {"GOOGLE_API_KEY=$($env:GOOGLE_API_KEY)" | Add-Content .env}
$recordingPath = [IO.Path]::GetFullPath((Join-Path $root "recordings"))
$transcriptPath = [IO.Path]::GetFullPath((Join-Path $root "transcripts"))
if (-not (Select-String -Path .env -Pattern '^VLOG_RECORDING_DIR=' -Quiet -ErrorAction SilentlyContinue)) {"VLOG_RECORDING_DIR=$recordingPath" | Add-Content .env}
if (-not (Select-String -Path .env -Pattern '^VLOG_TRANSCRIPT_DIR=' -Quiet -ErrorAction SilentlyContinue)) {"VLOG_TRANSCRIPT_DIR=$transcriptPath" | Add-Content .env}
$sdDevice = $null
if (-not (Select-String -Path .env -Pattern '^SD_INPUT_DEVICE=' -Quiet -ErrorAction SilentlyContinue)) {$sdDevice = Read-Host "SD_INPUT_DEVICE (input device index, blank to skip)"}
if ($sdDevice) {$env:SD_INPUT_DEVICE = $sdDevice; "SD_INPUT_DEVICE=$sdDevice" | Add-Content .env}
try { uv sync } catch { Write-Warning "uv sync failed: $_" }
$vbs = Join-Path $root "run_silent.vbs"
$launcherDir = Join-Path $env:LOCALAPPDATA "VlogAutoDiary"
New-Item -ItemType Directory -Force -Path $launcherDir | Out-Null
$launcher = Join-Path $launcherDir "launch.cmd"
try {
    Set-Content -Path $launcher -Value "@echo off`r`npushd `"$root`"`r`nwscript.exe `"$vbs`"`r`n" -Encoding ASCII
} catch { Write-Warning "Failed to write launcher: $_" }
try {
    schtasks /Create /TN "VlogAutoDiary" /TR "`"$launcher`"" /SC ONLOGON /RL HIGHEST /F /DELAY 0000:30 /RU "$env:USERNAME"
} catch { Write-Warning "schtasks failed (try running as admin if RL=HIGHEST is required): $_" }
try { Start-Process -FilePath $launcher } catch { Write-Warning "Failed to start launcher: $_" }
Start-Sleep -Seconds 5
try { if (Test-Path "vlog.log") {Get-Content "vlog.log" -Tail 20} } catch { Write-Warning "Reading vlog.log failed: $_" }
$ErrorActionPreference = "Continue"
