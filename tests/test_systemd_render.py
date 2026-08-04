from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "infra" / "systemd" / "render.py"
SPEC = importlib.util.spec_from_file_location("vlog_systemd_render", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_render_units_uses_supplied_repository_root(tmp_path: Path) -> None:
    repo = tmp_path / "checkout with space"
    repo.mkdir()
    (repo / "pyproject.toml").write_text("[project]\nname='vlog'\n", encoding="utf-8")
    output = tmp_path / "units"

    paths = MODULE.render_units(repo, output)

    assert {path.name for path in paths} == {
        "vlog.service",
        "vlog-monitor-failure.service",
        "vlog-daily.service",
        "vlog-daily-failure.service",
        "vlog-daily.timer",
    }
    monitor = (output / "vlog.service").read_text(encoding="utf-8")
    assert "@VLOG_" not in monitor
    assert "checkout\\x20with\\x20space" in monitor
    assert "/home/kafka/" not in monitor


def test_templates_do_not_commit_checkout_path() -> None:
    for template in (REPO_ROOT / "infra" / "systemd").glob("*.in"):
        content = template.read_text(encoding="utf-8")
        assert "%h/projects/vlog" not in content
        assert "/home/kafka/" not in content
