from src.infrastructure.settings import settings
from src.use_cases import daily_workload
from src.use_cases.daily_workload import collect_daily_workload, render_daily_workload


class StubResourceMonitor:
    def __init__(
        self,
        *,
        gpu_vram_free_mib: int | None = 8192,
        cpu_percent: float = 12.5,
        ready: bool = True,
        reason: str | None = None,
    ) -> None:
        self._gpu_vram_free_mib = gpu_vram_free_mib
        self._cpu_percent = cpu_percent
        self._ready = ready
        self._reason = reason

    def snapshot(self):
        return type(
            "Snapshot",
            (),
            {
                "gpu_vram_free_mib": self._gpu_vram_free_mib,
                "cpu_percent": self._cpu_percent,
            },
        )()

    def is_idle_for_heavy_work(self, *, snapshot=None, **_kwargs):
        return self._ready, self._reason, snapshot or self.snapshot()


class StubProcessMonitor:
    def is_running(self) -> bool:
        return False


def _patch_settings(monkeypatch, tmp_path, resource_monitor=None):
    recording_dir = tmp_path / "recordings"
    transcript_dir = tmp_path / "transcripts"
    summary_dir = tmp_path / "summaries"
    novel_dir = tmp_path / "novels"
    evaluation_dir = tmp_path / "evaluations"

    recording_dir.mkdir()
    transcript_dir.mkdir()
    summary_dir.mkdir()
    novel_dir.mkdir()
    evaluation_dir.mkdir()

    monkeypatch.setattr(settings, "recording_dir", recording_dir)
    monkeypatch.setattr(settings, "transcript_dir", transcript_dir)
    monkeypatch.setattr(settings, "summary_dir", summary_dir)
    monkeypatch.setattr(settings, "novel_out_dir", novel_dir)
    monkeypatch.setattr(settings, "photo_dir", tmp_path / "photos")
    monkeypatch.setattr(daily_workload, "COGNEE_QUEUE_PATH", tmp_path / "queue.yaml")
    monkeypatch.setattr(daily_workload, "ProcessMonitor", StubProcessMonitor)
    monkeypatch.setattr(
        daily_workload,
        "SystemResourceMonitor",
        lambda: resource_monitor or StubResourceMonitor(),
    )


def test_daily_workload_plan_reports_stage_vector(monkeypatch, tmp_path):
    _patch_settings(monkeypatch, tmp_path)
    settings.photo_dir.mkdir()

    recording_path = settings.recording_dir / "20260620_120000.flac"
    recording_path.write_text("audio", encoding="utf-8")
    (settings.transcript_dir / "cleaned_20260621_120000.txt").write_text(
        "transcript", encoding="utf-8"
    )
    (settings.summary_dir / "20260622_summary.txt").write_text(
        "summary", encoding="utf-8"
    )
    (settings.summary_dir / "20260623_summary.txt").write_text(
        "summary", encoding="utf-8"
    )
    (settings.novel_out_dir / "20260623.md").write_text("novel", encoding="utf-8")
    (settings.summary_dir / "20260624_summary.txt").write_text(
        "summary", encoding="utf-8"
    )
    (settings.novel_out_dir / "20260624.md").write_text("novel", encoding="utf-8")
    (settings.summary_dir.parent / "evaluations" / "20260623.json").write_text(
        "{}", encoding="utf-8"
    )
    daily_workload.COGNEE_QUEUE_PATH.write_text(
        """
batch_size: 3
files:
  - name: a.txt
    status: pending
    error: null
  - name: b.txt
    status: processing
    error: null
  - name: c.txt
    status: failed
    error: nope
""".strip(),
        encoding="utf-8",
    )

    plan = collect_daily_workload()

    assert plan.counts.recordings_pending == 1
    assert plan.counts.transcript_days_pending == 1
    assert plan.counts.summary_days_pending == 1
    assert plan.counts.novel_days_pending == 1
    assert plan.counts.cognee_pending == 1
    assert plan.counts.cognee_processing == 1
    assert plan.counts.cognee_failed == 1
    assert plan.counts.cognee_batch_size == 3
    assert plan.counts.workload_score == 8
    assert plan.counts.cognee_batches_remaining == 1
    assert plan.vrc_running is False
    assert plan.resource_ready is True
    assert plan.can_autorun_recording_flow is True
    assert plan.next_action == "transcribe"
    assert plan.next_action_target == 1
    assert plan.next_action_limit is None

    rendered = render_daily_workload(plan)
    assert "recordings_pending=1" in rendered
    assert "next_action=transcribe" in rendered
    assert "recording_flow=enabled" in rendered


def test_daily_workload_falls_back_to_cognee_batch(monkeypatch, tmp_path):
    _patch_settings(monkeypatch, tmp_path)
    daily_workload.COGNEE_QUEUE_PATH.write_text(
        """
batch_size: 5
files:
  - name: a.txt
    status: pending
    error: null
  - name: b.txt
    status: pending
    error: null
  - name: c.txt
    status: pending
    error: null
""".strip(),
        encoding="utf-8",
    )

    plan = collect_daily_workload()

    assert plan.next_action == "cognee_ingest"
    assert plan.next_action_target == 3
    assert plan.next_action_limit == 5


def test_daily_workload_limits_evaluation_batches(monkeypatch, tmp_path):
    _patch_settings(monkeypatch, tmp_path)
    daily_workload.COGNEE_QUEUE_PATH.write_text(
        """
batch_size: 5
files: []
""".strip(),
        encoding="utf-8",
    )
    (settings.summary_dir / "20260620_summary.txt").write_text(
        "summary", encoding="utf-8"
    )
    (settings.novel_out_dir / "20260620.md").write_text("novel", encoding="utf-8")

    plan = collect_daily_workload()

    assert plan.next_action == "evaluate"
    assert plan.next_action_target == 1
    assert plan.next_action_limit == 1


def test_daily_workload_pauses_recording_flow_when_cpu_busy(monkeypatch, tmp_path):
    resource_monitor = StubResourceMonitor(
        gpu_vram_free_mib=5000,
        cpu_percent=92.0,
        ready=False,
        reason="High CPU usage: 92.0% busy",
    )
    _patch_settings(monkeypatch, tmp_path, resource_monitor=resource_monitor)

    recording_path = settings.recording_dir / "20260620_120000.flac"
    recording_path.write_text("audio", encoding="utf-8")

    plan = collect_daily_workload()

    assert plan.counts.recordings_pending == 1
    assert plan.vrc_running is False
    assert plan.resource_ready is False
    assert plan.can_autorun_recording_flow is False
    assert plan.resource_reason == "High CPU usage: 92.0% busy"
    assert "recording_flow=paused" in render_daily_workload(plan)
