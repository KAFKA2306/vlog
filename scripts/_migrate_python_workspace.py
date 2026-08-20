#!/usr/bin/env python3
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPTURE_SRC = ROOT / "apps/capture-vrchat/src"
CAPTURE_PACKAGE = CAPTURE_SRC / "vlog_capture"


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.rstrip() + "\n", encoding="utf-8")


def migrate_capture_package() -> None:
    if not CAPTURE_PACKAGE.exists():
        CAPTURE_PACKAGE.mkdir()
        for child in list(CAPTURE_SRC.iterdir()):
            if child.name in {"README.md", "vlog_capture"}:
                continue
            shutil.move(str(child), str(CAPTURE_PACKAGE / child.name))


def rewrite_python_imports() -> None:
    for path in ROOT.rglob("*.py"):
        if any(part.startswith(".venv") for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        updated = re.sub(
            r"(?m)^(\s*from\s+)src(?=\.|\s+import)", r"\1vlog_capture", text
        )
        updated = re.sub(
            r"(?m)^(\s*import\s+)src(?=\.|\s|$)", r"\1vlog_capture", updated
        )
        updated = updated.replace('"vlog_capture.', '"vlog_capture.').replace(
            "'vlog_capture.", "'vlog_capture."
        )
        updated = updated.replace(
            '["uv", "run", "--frozen", "vlog", *args]',
            '["uv", "run", "--frozen", "vlog", *args]',
        )
        if updated != text:
            path.write_text(updated, encoding="utf-8")


def rewrite_runtime_assets() -> None:
    replacements = {
        "python -m src.main": "vlog-service",
        "python -m src.cli": "vlog",
        "python -m src.daily": "vlog-daily",
        "python -m src.scripts.audit_publication": "python -m vlog_capture.scripts.audit_publication",
        "apps/capture-vrchat/src/portability.py": "apps/capture-vrchat/src/vlog_capture/portability.py",
    }
    suffixes = {".md", ".yaml", ".yml", ".toml", ".ps1", ".bat", ".in", ".sh"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in suffixes:
            continue
        if any(part.startswith(".venv") for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        updated = text
        for old, new in replacements.items():
            updated = updated.replace(old, new)
        if updated != text:
            path.write_text(updated, encoding="utf-8")

    taskfile = ROOT / "Taskfile.yaml"
    text = taskfile.read_text(encoding="utf-8")
    text = re.sub(r"^\s+PYTHONPATH:.*\n", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s+LD_LIBRARY_PATH:.*\n", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s+- export PYTHONPATH=.*\n", "", text, flags=re.MULTILINE)
    text = text.replace("cmd: export PYTHONPATH=$PYTHONPATH:. && ", "cmd: ")
    text = text.replace("cmd: $UV sync --frozen", "cmd: $UV sync --locked --extra gpu")
    text = text.replace("$UV run python -m vlog_capture.cli", "$UV run --frozen vlog")
    text = text.replace(
        "$UV run python -m vlog_capture.main", "$UV run --frozen vlog-service"
    )
    text = text.replace(
        "$UV run python -m vlog_capture.daily", "$UV run --frozen vlog-daily"
    )
    text = text.replace(
        "$UV run python -m vlog_capture.scripts.audit_publication",
        "$UV run --frozen python -m vlog_capture.scripts.audit_publication",
    )
    taskfile.write_text(text, encoding="utf-8")

    run_bat = ROOT / "infra/windows/run.bat"
    text = run_bat.read_text(encoding="utf-8")
    text = re.sub(r'^set "PYTHONPATH=.*\n', "", text, flags=re.MULTILINE)
    text = text.replace(
        "run --frozen python -m vlog_capture.main", "run --frozen vlog-service"
    )
    run_bat.write_text(text, encoding="utf-8")

    render = ROOT / "infra/systemd/render.py"
    text = render.read_text(encoding="utf-8")
    text = re.sub(
        r'\n    pythonpath = ":"\.join\(\n        \(\n            f"\{root\}/apps/capture-vrchat",\n            f"\{root\}/packages/memory-domain/src",\n            f"\{root\}/packages/ingestion/src",\n        \)\n    \)\n',
        "\n",
        text,
    )
    text = text.replace(
        '        "@VLOG_PYTHONPATH@": escape_unit_value(pythonpath),\n', ""
    )
    render.write_text(text, encoding="utf-8")

    for path in (ROOT / "infra/systemd").glob("*.in"):
        text = path.read_text(encoding="utf-8")
        text = re.sub(
            r"^Environment=PYTHONPATH=@VLOG_PYTHONPATH@\n", "", text, flags=re.MULTILINE
        )
        text = text.replace(
            "@VLOG_UV@ run python -m vlog_capture.main",
            "@VLOG_UV@ run --frozen vlog-service",
        )
        text = text.replace(
            "@VLOG_UV@ run python -m vlog_capture.daily",
            "@VLOG_UV@ run --frozen vlog-daily",
        )
        text = text.replace(
            "@VLOG_UV@ run python -m vlog_capture.cli", "@VLOG_UV@ run --frozen vlog"
        )
        path.write_text(text, encoding="utf-8")

    ci = ROOT / ".github/workflows/test.yml"
    text = ci.read_text(encoding="utf-8")
    text = re.sub(r"^\s+PYTHONPATH:.*\n", "", text, flags=re.MULTILINE)
    old = """      - run: uv venv\n      - name: Install focused test dependencies\n        run: >-\n          uv pip install\n          pytest\n          pydantic-settings\n          pyyaml\n          python-dotenv\n          supabase\n          pillow\n          numpy\n          psutil\n          sounddevice\n          soundfile\n          google-generativeai\n"""
    text = text.replace(
        old,
        "      - name: Sync locked Python workspace\n        run: uv sync --locked\n",
    )
    text = text.replace("uv run --no-sync ", "uv run --no-sync ")
    text = text.replace(
        "apps/capture-vrchat/src/portability.py",
        "apps/capture-vrchat/src/vlog_capture/portability.py",
    )
    ci.write_text(text, encoding="utf-8")


def write_manifests() -> None:
    write(
        "pyproject.toml",
        """[project]
name = "vlog"
version = "0.1.0"
description = "VRChat Auto-Diary"
readme = "README.md"
requires-python = ">=3.12,<3.13"
dependencies = [
    "vlog-capture",
    "vlog-memory-domain",
    "vlog-ingestion",
    "vlog-companion",
    "vlog-privacy",
    "vlog-vrchat-osc",
]

[project.optional-dependencies]
gpu = ["vlog-capture[gpu]"]
cognee = ["cognee[all]>=1.0.0"]

[tool.uv.sources]
vlog-capture = { workspace = true }
vlog-memory-domain = { workspace = true }
vlog-ingestion = { workspace = true }
vlog-companion = { workspace = true }
vlog-privacy = { workspace = true }
vlog-vrchat-osc = { workspace = true }

[tool.uv.workspace]
members = [
    "apps/capture-vrchat",
    "packages/memory-domain",
    "packages/ingestion",
    "packages/companion",
    "packages/privacy",
    "adapters/vrchat-osc",
]

[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I"]
ignore = ["E501"]

[dependency-groups]
dev = [
    "codd-dev>=2.18.0",
    "pytest>=9.0.2",
    "ruff>=0.14.9",
    "ty>=0.0.64",
]
""",
    )

    write(
        "apps/capture-vrchat/pyproject.toml",
        """[project]
name = "vlog-capture"
version = "0.1.0"
description = "VLog VRChat capture and processing runtime"
requires-python = ">=3.12,<3.13"
dependencies = [
    "google-generativeai>=0.8.0",
    "numpy>=1.26.0",
    "pillow>=12.0.0",
    "platformdirs>=4.3.0",
    "psutil>=5.9.0",
    "pydantic-settings>=2.12.0",
    "python-dotenv>=1.0.0",
    "pyyaml>=6.0.3",
    "sounddevice>=0.4.6",
    "soundfile>=0.12.1",
    "supabase>=2.0.0",
    "vlog-companion",
    "vlog-ingestion",
    "vlog-memory-domain",
    "vlog-privacy",
    "vlog-vrchat-osc",
]

[project.optional-dependencies]
gpu = [
    "accelerate>=1.1.1",
    "diffusers @ git+https://github.com/huggingface/diffusers",
    "faster-whisper>=0.10.0",
    "huggingface-hub>=0.26.2",
    "nvidia-cublas-cu12>=12.1.3.1",
    "nvidia-cudnn-cu12>=9.1.0.70",
    "sentencepiece>=0.2.0",
    "torch>=2.5.1",
    "transformers>=4.46.3",
]

[project.scripts]
vlog = "vlog_capture.cli:main"
vlog-service = "vlog_capture.main:main"
vlog-daily = "vlog_capture.daily:main"

[build-system]
requires = ["uv_build>=0.12.5,<0.13"]
build-backend = "uv_build"
""",
    )

    manifests = {
        "packages/memory-domain/pyproject.toml": """[project]
name = "vlog-memory-domain"
version = "0.1.0"
requires-python = ">=3.12,<3.13"
dependencies = []

[build-system]
requires = ["uv_build>=0.12.5,<0.13"]
build-backend = "uv_build"
""",
        "packages/ingestion/pyproject.toml": """[project]
name = "vlog-ingestion"
version = "0.1.0"
requires-python = ">=3.12,<3.13"
dependencies = ["vlog-memory-domain"]

[build-system]
requires = ["uv_build>=0.12.5,<0.13"]
build-backend = "uv_build"
""",
        "packages/companion/pyproject.toml": """[project]
name = "vlog-companion"
version = "0.1.0"
requires-python = ">=3.12,<3.13"
dependencies = []

[build-system]
requires = ["uv_build>=0.12.5,<0.13"]
build-backend = "uv_build"
""",
        "packages/privacy/pyproject.toml": """[project]
name = "vlog-privacy"
version = "0.1.0"
requires-python = ">=3.12,<3.13"
dependencies = ["vlog-memory-domain"]

[build-system]
requires = ["uv_build>=0.12.5,<0.13"]
build-backend = "uv_build"
""",
        "adapters/vrchat-osc/pyproject.toml": """[project]
name = "vlog-vrchat-osc"
version = "0.1.0"
requires-python = ">=3.12,<3.13"
dependencies = []

[build-system]
requires = ["uv_build>=0.12.5,<0.13"]
build-backend = "uv_build"
""",
    }
    for path, content in manifests.items():
        write(path, content)


def fix_service_main() -> None:
    path = CAPTURE_PACKAGE / "main.py"
    text = path.read_text(encoding="utf-8")
    old = """if __name__ == "__main__":\n    setup_logging()\n    app = Application()\n    app.run()\n"""
    new = """def main() -> None:\n    setup_logging()\n    app = Application()\n    app.run()\n\n\nif __name__ == "__main__":\n    main()\n"""
    if old in text:
        path.write_text(text.replace(old, new), encoding="utf-8")


def assert_no_runtime_pythonpath() -> None:
    candidates = [
        ROOT / "Taskfile.yaml",
        ROOT / ".github/workflows/test.yml",
        ROOT / "infra/windows/run.bat",
        ROOT / "infra/systemd/render.py",
        *list((ROOT / "infra/systemd").glob("*.in")),
    ]
    offenders = [
        str(path.relative_to(ROOT))
        for path in candidates
        if "PYTHONPATH" in path.read_text(encoding="utf-8")
    ]
    if offenders:
        raise SystemExit("runtime PYTHONPATH remains in: " + ", ".join(offenders))


def main() -> None:
    migrate_capture_package()
    rewrite_python_imports()
    rewrite_runtime_assets()
    write_manifests()
    fix_service_main()
    assert_no_runtime_pythonpath()
    subprocess.run(["git", "status", "--short"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
