from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WINDOWS_DIR = ROOT / "infra" / "windows"


def _read(name: str) -> str:
    return (WINDOWS_DIR / name).read_text(encoding="utf-8")


def test_root_launchers_delegate_to_windows_implementation() -> None:
    assert (ROOT / "run.bat").read_text(encoding="utf-8") == (
        '@echo off\ncall "%~dp0infra\\windows\\run.bat" %*\nexit /b %ERRORLEVEL%\n'
    )
    assert (ROOT / "bootstrap.bat").read_text(encoding="utf-8") == (
        '@echo off\ncall "%~dp0infra\\windows\\bootstrap.bat" %*\nexit /b %ERRORLEVEL%\n'
    )


def test_windows_launcher_requires_native_checkout_and_restores_directory() -> None:
    script = _read("run.bat")
    assert 'set "PROJECT_ROOT=%~dp0..\\.."' in script
    assert 'if "%PROJECT_ROOT:~0,2%"=="\\\\" (' in script
    assert "Windows-native drive" in script
    assert 'pushd "%PROJECT_ROOT%" 2>nul' in script
    assert 'if not exist "pyproject.toml" (' in script
    assert "popd\nexit /b %EXIT_CODE%" in script


def test_windows_launcher_uses_resolved_uv_and_dynamic_nvidia_paths() -> None:
    script = _read("run.bat")
    assert "VLOG_UV_EXE" in script
    assert "where uv.exe" in script
    assert "import pathlib,nvidia.cudnn" in script
    assert "import pathlib,nvidia.cublas" in script
    assert "python3.12\\site-packages\\nvidia" not in script


def test_task_registration_sets_absolute_action_and_working_directory() -> None:
    script = _read("register_task.ps1")
    assert '$ErrorActionPreference = "Stop"' in script
    assert "Resolve-Path -LiteralPath $RunScript).ProviderPath" in script
    assert "Get-Command cmd.exe" in script
    assert "Get-Command uv.exe" in script
    assert "-WorkingDirectory $repoRoot" in script
    assert "requires a Windows-native checkout" in script


def test_windows_guide_documents_native_checkout_and_legacy_data_bridge() -> None:
    guide = _read("README.md")
    assert "Windows native drive" in guide
    assert "Git commit SHA" in guide
    assert "legacy `data/` bridge" in guide
    assert "shared **code checkout**" in guide
