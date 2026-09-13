from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "infra" / "systemd" / "install.sh"


def _fake_executable(path: Path, output: str) -> None:
    path.write_text(f"#!/bin/sh\nprintf '%s\\n' '{output}'\n", encoding="utf-8")
    path.chmod(0o755)


def test_installer_diagnose_resolves_binaries_with_minimal_path(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _fake_executable(bin_dir / "uv", "uv 9.9.9")
    _fake_executable(bin_dir / "systemctl", "systemd 999")

    result = subprocess.run(
        ["/bin/bash", str(INSTALLER), "--diagnose"],
        cwd=REPO_ROOT,
        env={"PATH": str(bin_dir), "HOME": str(tmp_path)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert f"resolved uv: {bin_dir / 'uv'} (uv 9.9.9)" in result.stdout
    assert f"resolved systemctl: {bin_dir / 'systemctl'} (systemd 999)" in result.stdout


def test_installer_fails_before_registration_when_systemctl_is_missing(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _fake_executable(bin_dir / "uv", "uv 9.9.9")

    result = subprocess.run(
        ["/bin/bash", str(INSTALLER), "--diagnose"],
        cwd=REPO_ROOT,
        env={"PATH": str(bin_dir), "HOME": str(tmp_path)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "systemctl executable was not found" in result.stderr
