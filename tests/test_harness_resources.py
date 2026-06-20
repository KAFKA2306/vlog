from types import SimpleNamespace

from src.domain.harness import TaskWeight
from src.infrastructure import harness


class StubProcessMonitor:
    def is_running(self) -> bool:
        return False


class StubResourceMonitor:
    def __init__(self, *, ready: bool, reason: str | None):
        self._ready = ready
        self._reason = reason

    def is_idle_for_heavy_work(self, *, snapshot=None, **_kwargs):
        snapshot = snapshot or SimpleNamespace(gpu_vram_free_mib=5000, cpu_percent=12.5)
        return self._ready, self._reason, snapshot


def test_guarddog_blocks_heavy_work_when_cpu_busy(monkeypatch):
    monkeypatch.setattr(harness, "ProcessMonitor", StubProcessMonitor)
    monkeypatch.setattr(
        harness,
        "SystemResourceMonitor",
        lambda: StubResourceMonitor(ready=False, reason="High CPU usage: 92.0% busy"),
    )
    monkeypatch.setattr(
        harness.shutil,
        "disk_usage",
        lambda _path: SimpleNamespace(free=10 * 1024**3),
    )

    safe, reason = harness.GuardDog().check_safety(TaskWeight.HEAVY)

    assert safe is False
    assert reason == "High CPU usage: 92.0% busy"


def test_guarddog_allows_heavy_work_when_resources_are_idle(monkeypatch):
    monkeypatch.setattr(harness, "ProcessMonitor", StubProcessMonitor)
    monkeypatch.setattr(
        harness,
        "SystemResourceMonitor",
        lambda: StubResourceMonitor(ready=True, reason=None),
    )
    monkeypatch.setattr(
        harness.shutil,
        "disk_usage",
        lambda _path: SimpleNamespace(free=10 * 1024**3),
    )

    safe, reason = harness.GuardDog().check_safety(TaskWeight.HEAVY)

    assert safe is True
    assert reason is None
