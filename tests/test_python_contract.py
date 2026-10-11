from pathlib import Path

from scripts import check_python_contract as contract


def write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def consistent_tree(root: Path) -> None:
    write(root, ".python-version", "3.12\n")
    write(root, "pyproject.toml", '[project]\nrequires-python = ">=3.12,<3.13"\n')
    write(
        root,
        "packages/a/pyproject.toml",
        '[project]\nrequires-python = ">=3.12,<3.13"\n',
    )
    write(root, "uv.lock", 'requires-python = "==3.12.*"\n')
    write(
        root,
        ".github/workflows/test.yml",
        "python-version: '3.12'\npython-version: '3.12'\n",
    )
    write(root, "infra/windows/run.bat", 'set "UV_PYTHON=3.12"\n')
    write(
        root, ".devcontainer/Dockerfile", "FROM x-3.12-bookworm\nENV UV_PYTHON=3.12\n"
    )


def test_repository_python_contract_is_consistent() -> None:
    assert contract.violations(contract.ROOT) == []


def test_consistent_tree_passes(tmp_path: Path) -> None:
    consistent_tree(tmp_path)
    assert contract.violations(tmp_path) == []


def test_divergent_requires_python_is_reported(tmp_path: Path) -> None:
    consistent_tree(tmp_path)
    write(
        tmp_path, "packages/a/pyproject.toml", '[project]\nrequires-python = ">=3.11"\n'
    )
    assert any("requires-python" in item for item in contract.violations(tmp_path))


def test_python_version_file_outside_range_is_reported(tmp_path: Path) -> None:
    consistent_tree(tmp_path)
    write(tmp_path, ".python-version", "3.11\n")
    assert any(".python-version" in item for item in contract.violations(tmp_path))


def test_ci_version_outside_range_is_reported(tmp_path: Path) -> None:
    consistent_tree(tmp_path)
    write(tmp_path, ".github/workflows/test.yml", "python-version: '3.13'\n")
    assert any("test.yml" in item for item in contract.violations(tmp_path))


def test_uv_python_outside_range_is_reported(tmp_path: Path) -> None:
    consistent_tree(tmp_path)
    write(tmp_path, "infra/windows/run.bat", 'set "UV_PYTHON=3.11"\n')
    assert any("run.bat" in item for item in contract.violations(tmp_path))


def test_minor_version_path_in_runtime_is_reported(tmp_path: Path) -> None:
    consistent_tree(tmp_path)
    write(tmp_path, "scripts/x.sh", "LD=venv/lib/python3.11/site-packages\n")
    assert any("x.sh" in item for item in contract.violations(tmp_path))
