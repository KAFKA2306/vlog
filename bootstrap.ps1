param([switch]$NoSchedule)

if ($env:OS -ne 'Windows_NT') { exit 1 }

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$envRoot = $root
if ($root -like "\\*") {
  $driveLetter = "Z:"
  cmd /c "net use $driveLetter `"$root`" /persistent:no >nul 2>&1"
  if (Test-Path $driveLetter) { $envRoot = "$driveLetter\" }
}
Set-Location -LiteralPath $envRoot

$env:UV_PROJECT_ENVIRONMENT = ".venv-win"
$env:UV_LINK_MODE = "copy"

if (Test-Path ".env.example") {
  if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
  }
}

if (-not (Test-Path ".env")) {
  New-Item -ItemType File -Path ".env" | Out-Null
}

$recordingPath = [IO.Path]::GetFullPath((Join-Path $root "recordings"))
$transcriptPath = [IO.Path]::GetFullPath((Join-Path $root "transcripts"))
if (-not (Select-String -Path .env -Pattern '^VLOG_RECORDING_DIR=' -Quiet)) { "VLOG_RECORDING_DIR=$recordingPath" | Add-Content .env }
if (-not (Select-String -Path .env -Pattern '^VLOG_TRANSCRIPT_DIR=' -Quiet)) { "VLOG_TRANSCRIPT_DIR=$transcriptPath" | Add-Content .env }

$launcherDir = Join-Path $env:LOCALAPPDATA "VlogAutoDiary"
New-Item -ItemType Directory -Force -Path $launcherDir | Out-Null
$vbs = Join-Path $root "run_silent.vbs"
$launcher = Join-Path $launcherDir "launch.cmd"
Set-Content -Path $launcher -Value "@echo off`r`npushd `"$root`"`r`nwscript.exe `"$vbs`"`r`n" -Encoding ASCII

if (-not $NoSchedule) {
  schtasks /Create /TN "VlogAutoDiary" /TR "`"$launcher`"" /SC ONLOGON /RL HIGHEST /F /DELAY 0000:30 /RU "$env:USERNAME"
  Start-Process -FilePath $launcher
}
