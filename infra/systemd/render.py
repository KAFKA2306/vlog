#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

from platformdirs import PlatformDirs

TEMPLATE_DIR = Path(__file__).resolve().parent
UNIT_SUFFIXES = (".service.in", ".timer.in")


def find_repository_root() -> Path:
    return TEMPLATE_DIR.parents[1]


def escape_unit_value(value: str) -> str:
    """Escape a value used in an unquoted systemd unit directive."""

    escaped: list[str] = []
    for char in value:
        if char == "%":
            escaped.append("%%")
        elif char.isalnum() or char in "/._:-":
            escaped.append(char)
        elif ord(char) <= 0xFF:
            escaped.append(f"\\x{ord(char):02x}")
        else:
            escaped.append(char)
    return "".join(escaped)


def resolve_uv_path(explicit: Path | None = None) -> Path:
    candidate = explicit or (Path(found) if (found := shutil.which("uv")) else None)
    if candidate is None:
        raise ValueError("uv executable was not found; install uv or pass --uv")
    resolved = candidate.expanduser().resolve()
    if not resolved.is_file():
        raise ValueError(f"uv executable does not exist: {resolved}")
    return resolved


def resolve_runtime_homes() -> dict[str, Path]:
    roaming = PlatformDirs(appname="vlog", appauthor=False, roaming=True)
    local = PlatformDirs(appname="vlog", appauthor=False)
    defaults = {
        "config": Path(roaming.user_config_dir),
        "data": Path(local.user_data_dir),
        "state": Path(roaming.user_state_dir),
        "cache": Path(local.user_cache_dir),
    }
    return {
        name: Path(os.environ.get(f"VLOG_{name.upper()}_HOME", default))
        .expanduser()
        .resolve()
        for name, default in defaults.items()
    }


def env_file_directive() -> str:
    raw = os.environ.get("VLOG_ENV_FILE")
    if not raw:
        return "# VLOG_ENV_FILE is not configured"
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise ValueError("VLOG_ENV_FILE must be an absolute path")
    return f"EnvironmentFile=-{escape_unit_value(str(path.resolve()))}"


def render_units(
    root: Path,
    output: Path,
    uv_path: Path | None = None,
) -> list[Path]:
    root = root.expanduser().resolve()
    if not (root / "pyproject.toml").is_file():
        raise ValueError(f"not a VLog repository: {root}")

    uv = resolve_uv_path(uv_path)
    homes = resolve_runtime_homes()
    replacements = {
        "@VLOG_ROOT@": escape_unit_value(str(root)),
        "@VLOG_UV@": escape_unit_value(str(uv)),
        "@VLOG_CONFIG_HOME@": escape_unit_value(str(homes["config"])),
        "@VLOG_DATA_HOME@": escape_unit_value(str(homes["data"])),
        "@VLOG_STATE_HOME@": escape_unit_value(str(homes["state"])),
        "@VLOG_CACHE_HOME@": escape_unit_value(str(homes["cache"])),
        "@VLOG_ENV_FILE_DIRECTIVE@": env_file_directive(),
    }
    output.mkdir(parents=True, exist_ok=True)

    rendered: list[Path] = []
    for template in sorted(TEMPLATE_DIR.iterdir()):
        if not template.name.endswith(UNIT_SUFFIXES):
            continue
        destination = output / template.name.removesuffix(".in")
        content = template.read_text(encoding="utf-8")
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)
        if "@VLOG_" in content:
            raise ValueError(f"unresolved placeholder in {template}")
        destination.write_text(content, encoding="utf-8")
        rendered.append(destination)
    return rendered


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render portable VLog systemd units.")
    parser.add_argument("--root", type=Path, default=find_repository_root())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--uv", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    for path in render_units(
        args.root,
        args.output.expanduser().resolve(),
        args.uv,
    ):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
