import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_MINORS = {(3, 12)}
PIN_PATTERNS = (
    re.compile(r"python-version:\s*['\"]?(\d+\.\d+)"),
    re.compile(r"UV_PYTHON=(\d+\.\d+)"),
    re.compile(r"FROM\s+\S*-(\d+\.\d+)-"),
)
PIN_FILES = (".github/workflows", "infra/windows", ".devcontainer")
MINOR_PATH = re.compile(r"python3\.\d+")
MINOR_PATH_PREFIXES = (
    "scripts/",
    "infra/",
    "apps/capture-vrchat/src/",
    "Taskfile.yaml",
)
SELF = {"scripts/check_python_contract.py", "scripts/check_runtime_contract.py"}


def minor(text: str) -> tuple[int, int]:
    major, minor_ = text.split(".")[:2]
    return int(major), int(minor_)


def declared_ranges(root: Path) -> dict[str, str]:
    ranges = {}
    for path in sorted(root.rglob("pyproject.toml")):
        relative = path.relative_to(root).as_posix()
        if relative.startswith((".", "node_modules", "apps/reader", ".venv")):
            continue
        value = (
            tomllib.loads(path.read_text(encoding="utf-8"))
            .get("project", {})
            .get("requires-python")
        )
        if value:
            ranges[relative] = value
    return ranges


def pin_files(root: Path) -> list[Path]:
    return [
        path
        for base in PIN_FILES
        for path in sorted((root / base).rglob("*"))
        if path.is_file()
    ]


def runtime_files(root: Path) -> list[Path]:
    files = [root / "Taskfile.yaml"]
    for prefix in MINOR_PATH_PREFIXES[:3]:
        base = root / prefix
        files.extend(sorted(p for p in base.rglob("*") if p.is_file()))
    return [p for p in files if p.is_file()]


def violations(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    ranges = declared_ranges(root)
    if len(set(ranges.values())) > 1:
        failures.append(f"requires-python differs across projects: {ranges}")

    lock = root / "uv.lock"
    if lock.is_file():
        match = re.search(
            r'^requires-python = "==(\d+\.\d+)\.\*"', lock.read_text(), re.M
        )
        if match is None or minor(match[1]) not in SUPPORTED_MINORS:
            failures.append("uv.lock requires-python is outside the supported range")

    version_file = root / ".python-version"
    if (
        version_file.is_file()
        and minor(version_file.read_text().strip()) not in SUPPORTED_MINORS
    ):
        failures.append(
            f".python-version {version_file.read_text().strip()} is outside the supported range"
        )

    for path in pin_files(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in PIN_PATTERNS:
            for found in pattern.findall(text):
                if minor(found) not in SUPPORTED_MINORS:
                    failures.append(
                        f"{path.relative_to(root).as_posix()}: Python {found} is outside the supported range"
                    )

    for path in runtime_files(root):
        relative = path.relative_to(root).as_posix()
        if relative in SELF:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for found in MINOR_PATH.findall(text):
            failures.append(f"{relative}: embeds minor-version path {found!r}")
    return failures


def main() -> int:
    failures = violations()
    for failure in failures:
        print(f"python-contract-check: FAIL: {failure}")
    if not failures:
        print("python-contract-check: PASS")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
