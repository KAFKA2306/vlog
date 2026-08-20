#!/usr/bin/env python3
"""Read-only VLog portability and runtime preflight diagnostics."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from vlog_capture.portability import (
    classify_path,
    foreign_absolute_reason,
    runtime_directories,
    shared_checkout_reason,
)

SCRIPT_ROOT = Path(__file__).resolve().parents[1]


def project_root() -> tuple[Path, str]:
    configured = os.environ.get("VLOG_PROJECT_ROOT")
    if configured:
        root = Path(configured).expanduser().resolve()
        source = "VLOG_PROJECT_ROOT"
    else:
        root = SCRIPT_ROOT
        source = "script_location"
    if not (root / "pyproject.toml").is_file():
        raise RuntimeError(f"not a VLog repository: {root}")
    return root, source


def git_value(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def module_origin(name: str) -> str | None:
    try:
        spec = importlib.util.find_spec(name)
    except (ImportError, ModuleNotFoundError, ValueError):
        return None
    return None if spec is None else spec.origin or str(spec.submodule_search_locations)


def tool(name: str) -> dict[str, str | None]:
    path = shutil.which(name)
    version: str | None = None
    if path:
        try:
            result = subprocess.run(
                [path, "--version"],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=5,
            )
            version = (
                result.stdout.strip().splitlines()[0] if result.stdout.strip() else None
            )
        except (OSError, subprocess.TimeoutExpired):
            version = None
    return {"path": path, "version": version}


def configured_environment_names() -> list[str]:
    return sorted(
        name
        for name in os.environ
        if name.startswith("VLOG_") or name in {"SUPABASE_URL", "GOOGLE_API_KEY"}
    )


def redact_path(value: str, enabled: bool) -> str:
    if not enabled:
        return value
    home = str(Path.home())
    return value.replace(home, "~") if home else value


def collect(*, redact: bool = False) -> dict[str, Any]:
    root, root_source = project_root()
    runtime = platform.system()
    dirs = runtime_directories(system=runtime)
    dirty = git_value(root, "status", "--porcelain")
    root_text = str(root)

    tools = {
        name: tool(name)
        for name in (
            "git",
            "uv",
            "python",
            "task",
            "bun",
            "pwsh",
            "powershell",
            "systemctl",
        )
    }
    if redact:
        for item in tools.values():
            if item["path"]:
                item["path"] = redact_path(str(item["path"]), True)

    return {
        "status": "ok",
        "os": runtime,
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "python_runtime": platform.python_version(),
        "is_wsl": bool(
            os.environ.get("WSL_DISTRO_NAME")
            or "microsoft" in platform.release().lower()
        ),
        "cwd": redact_path(str(Path.cwd()), redact),
        "project_root": redact_path(root_text, redact),
        "project_root_source": root_source,
        "project_root_flavor": classify_path(root_text).value,
        "foreign_path": foreign_absolute_reason(root_text, system=runtime),
        "shared_checkout": shared_checkout_reason(root_text, system=runtime),
        "git": {
            "sha": git_value(root, "rev-parse", "HEAD"),
            "ref": git_value(root, "branch", "--show-current"),
            "dirty": bool(dirty),
        },
        "configuration": {
            "present_names": configured_environment_names(),
            "secret_values_exposed": False,
        },
        "runtime_directories": {
            "config": redact_path(str(dirs.config), redact),
            "state": redact_path(str(dirs.state), redact),
            "cache": redact_path(str(dirs.cache), redact),
        },
        "installed_packages": {
            "vlog_capture": module_origin("vlog_capture"),
            "vlog_memory_domain": module_origin("vlog_memory_domain"),
            "vlog_ingestion": module_origin("vlog_ingestion"),
            "vlog_companion": module_origin("vlog_companion"),
            "vlog_privacy": module_origin("vlog_privacy"),
            "vlog_vrchat_osc": module_origin("vlog_vrchat_osc"),
        },
        "tools": tools,
        "gpu_python_libraries": {
            "nvidia.cublas.lib": module_origin("nvidia.cublas.lib"),
            "nvidia.cudnn.lib": module_origin("nvidia.cudnn.lib"),
        },
        "host_checks": {
            "windows_task_scheduler": "available"
            if runtime == "Windows" and shutil.which("schtasks")
            else "not_checked",
            "systemd_user_manager": "available"
            if runtime == "Linux" and shutil.which("systemctl")
            else "not_checked",
            "vrchat_process": "requires_actual_windows_host",
            "physical_audio": "requires_actual_host",
            "gpu_transcription": "requires_actual_gpu_run",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json", action="store_true", help="emit machine-readable JSON"
    )
    parser.add_argument(
        "--redact", action="store_true", help="replace the user home in paths"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="fail on foreign/shared canonical checkout",
    )
    args = parser.parse_args()
    try:
        report = collect(redact=args.redact)
    except RuntimeError as exc:
        print(f"vlog-doctor: FAIL: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"VLog doctor: {report['os']} {report['architecture']}")
        print(f"project: {report['project_root']} ({report['project_root_source']})")
        print(
            f"git: {report['git']['sha']} ref={report['git']['ref']} "
            f"dirty={report['git']['dirty']}"
        )
        print(f"path flavor: {report['project_root_flavor']}")
        for key in ("foreign_path", "shared_checkout"):
            if report[key]:
                print(f"warning: {report[key]}")
        print("runtime dirs:")
        for key, value in report["runtime_directories"].items():
            print(f"  {key}: {value}")
        print("tools:")
        for name, info in report["tools"].items():
            detail = info["version"] or "version unknown"
            print(f"  {name}: {info['path'] or 'missing'} ({detail})")

    if args.strict and (report["foreign_path"] or report["shared_checkout"]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
