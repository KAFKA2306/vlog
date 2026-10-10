import subprocess
from pathlib import Path

import pytest
from vlog_capture.portability import checkout_identity_reason, shared_checkout_reason
from vlog_capture.project import find_project_root


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@pytest.fixture
def topology(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("VLOG_PROJECT_ROOT", raising=False)
    origin = tmp_path / "origin"
    origin.mkdir()
    git(origin, "init", "-q", "-b", "main")
    (origin / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (origin / "data").mkdir()
    (origin / "data" / ".gitkeep").write_text("", encoding="utf-8")
    git(origin, "add", "-A")
    git(origin, "commit", "-q", "-m", "init")
    windows_root = tmp_path / "windows-native" / "C" / "vlog"
    linux_root = tmp_path / "linux-native" / "home" / "vlog"
    for root in (windows_root, linux_root):
        root.parent.mkdir(parents=True)
        git(tmp_path, "clone", "-q", str(origin), str(root))
    return origin, windows_root, linux_root


def test_independent_checkouts_share_one_commit_sha(topology) -> None:
    origin, windows_root, linux_root = topology
    expected = git(origin, "rev-parse", "HEAD")
    assert git(windows_root, "rev-parse", "HEAD") == expected
    assert git(linux_root, "rev-parse", "HEAD") == expected
    assert checkout_identity_reason(windows_root, linux_root) is None


def test_checkouts_do_not_reference_each_others_physical_path(topology) -> None:
    _, windows_root, linux_root = topology
    for own, other in ((windows_root, linux_root), (linux_root, windows_root)):
        config = (own / ".git" / "config").read_text(encoding="utf-8")
        assert str(other) not in config
        assert str(other) not in git(own, "remote", "-v")
        assert not (own / ".git" / "objects" / "info" / "alternates").exists()


def test_each_checkout_resolves_its_own_root_without_the_other(
    topology, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, windows_root, linux_root = topology
    marker = windows_root / "apps" / "x.py"
    marker.parent.mkdir()
    marker.write_text("", encoding="utf-8")
    assert find_project_root(marker) == windows_root.resolve()
    assert find_project_root(linux_root / "pyproject.toml") == linux_root.resolve()


def test_identity_reason_flags_divergent_sha_and_shared_path(topology) -> None:
    _, windows_root, linux_root = topology
    (linux_root / "extra.txt").write_text("x", encoding="utf-8")
    git(linux_root, "add", "-A")
    git(linux_root, "commit", "-q", "-m", "diverge")
    assert "differ" in checkout_identity_reason(windows_root, linux_root)
    assert checkout_identity_reason(windows_root, windows_root) == (
        "checkouts must be independent roots"
    )


def test_cross_filesystem_checkout_is_not_a_native_root() -> None:
    assert shared_checkout_reason("/mnt/c/Users/x/vlog", system="Linux")
    assert shared_checkout_reason("/home/x/vlog", system="Linux") is None
