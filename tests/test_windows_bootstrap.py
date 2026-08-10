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


def test_windows_launchers_fail_closed_when_project_directory_is_unavailable() -> None:
    for name in ("run.bat", "bootstrap.bat"):
        script = _read(name)
        assert 'pushd "%PROJECT_ROOT%" 2>nul' in script
        assert "if errorlevel 1 (" in script
        assert "Could not open the project directory" in script
        assert "UNC or WSL share" in script
        assert 'if not exist "pyproject.toml" (' in script
        assert "exit /b 1" in script


def test_windows_launchers_restore_directory_after_success() -> None:
    run_script = _read("run.bat")
    bootstrap_script = _read("bootstrap.bat")

    assert "popd\nexit /b %EXIT_CODE%" in run_script
    assert ":failed\npopd\nexit /b 1" in bootstrap_script
    assert "popd\npause\nexit /b 0" in bootstrap_script


def test_windows_guide_explains_unc_mapping_and_failure_mode() -> None:
    guide = _read("README.md")
    assert "UNC" in guide
    assert "pushd" in guide
    assert "一時ドライブ" in guide


def test_task_registration_uses_a_windows_filesystem_path_and_stops_on_errors() -> None:
    script = (WINDOWS_DIR / "register_task.ps1").read_text(encoding="utf-8")
    assert '$ErrorActionPreference = "Stop"' in script
    assert "Resolve-Path -LiteralPath $RunScript).ProviderPath" in script
