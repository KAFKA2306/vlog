#!/usr/bin/env python3
"""Finalize the runtime-home migration on the temporary PR branch."""

from __future__ import annotations

from pathlib import Path


def replace(path: str, old: str, new: str, *, count: int = -1) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"{path}: missing expected fragment {old[:120]!r}")
    target.write_text(text.replace(old, new, count), encoding="utf-8")


def main() -> None:
    task_path = "Taskfile.yaml"
    pairs = [
        (
            "task photo novel=data/novels/YYYYMMDD.md 小説から画像生成",
            'task photo novel="$VLOG_DATA_HOME/novels/YYYYMMDD.md" 小説から画像生成',
        ),
        (
            "      $UV run --frozen python -c \"\n      import yaml\n      q = yaml.safe_load(open('data/cognee_queue.yaml'))\n      files = q['files']\n      total = len(files)\n      stats = {}\n      for f in files:\n          stats[f['status']] = stats.get(f['status'], 0) + 1\n      print(f'Total: {total}')\n      for s in ['completed','pending','processing','failed']:\n          if s in stats: print(f'  {s}: {stats[s]}')\n      failed = [f for f in files if f['status'] == 'failed']\n      if failed:\n          print('Failed files:')\n          for f in failed:\n              print(f'  - {f[\\\"name\\\"]}: {f[\\\"error\\\"]}')\n      \"",
            "      $UV run --frozen python scripts/cognee_status.py",
        ),
        (
            "- $UV run --frozen vlog image-generate --novel-file {{.novel}} --output-file data/photos/$(basename {{.novel}} .md).png",
            '- $UV run --frozen vlog image-generate --novel-file {{.novel}} --output-file "{{.VLOG_DATA_HOME}}/photos/$(basename {{.novel}} .md).png"',
        ),
        (
            "msg: novel=data/novels/YYYYMMDD.mdを指定してください",
            "msg: novel=<runtime-data>/novels/YYYYMMDD.mdを指定してください",
        ),
        (
            '- for f in data/novels/*.md; do [ -f "$f" ] && task photo novel="$f"; done || true',
            '- for f in "{{.VLOG_DATA_HOME}}"/novels/*.md; do [ -f "$f" ] && task photo novel="$f"; done || true',
        ),
        (
            '- for f in data/novels/*.md; do [ -f "$f" ] && task manga novel="$f"; done || true',
            '- for f in "{{.VLOG_DATA_HOME}}"/novels/*.md; do [ -f "$f" ] && task manga novel="$f"; done || true',
        ),
        (
            'test -d data/skills/vlog_user && echo "✅ vlog_user skill: EXISTS" || echo "❌ vlog_user skill: NOT FOUND"',
            'test -d "{{.VLOG_DATA_HOME}}/skills/vlog_user" && echo "✅ vlog_user skill: EXISTS" || echo "❌ vlog_user skill: NOT FOUND"',
        ),
        (
            'test -f /tmp/vlog-daily.log && tail -20 /tmp/vlog-daily.log || echo "No log file yet"',
            'test -f "{{.VLOG_STATE_HOME}}/logs/vlog-daily.log" && tail -20 "{{.VLOG_STATE_HOME}}/logs/vlog-daily.log" || echo "No log file yet"',
        ),
        (
            'rm -f /tmp/vlog-daily.log && echo "✅ Log cleared"',
            'rm -f "{{.VLOG_STATE_HOME}}/logs/vlog-daily.log" && echo "✅ Log cleared"',
        ),
    ]
    for old, new in pairs:
        replace(task_path, old, new)

    path = "apps/capture-vrchat/src/vlog_capture/cli_handlers.py"
    replace(
        path,
        "from vlog_capture.infrastructure.repositories import (\n    FileRepository,\n    SupabaseRepository,\n    TaskRepository,\n)\nfrom vlog_capture.infrastructure.system import (",
        "from vlog_capture.infrastructure.repositories import (\n    FileRepository,\n    SupabaseRepository,\n    TaskRepository,\n)\nfrom vlog_capture.infrastructure.settings import settings\nfrom vlog_capture.infrastructure.system import (",
    )
    replace(
        path,
        "from vlog_capture.use_cases.build_novel import BuildNovelUseCase\n",
        "from vlog_capture.portability import runtime_directories\nfrom vlog_capture.use_cases.build_novel import BuildNovelUseCase\n",
    )
    replace(
        path,
        "from vlog_capture.infrastructure.system import (\n    ProcessMonitor,",
        "from vlog_capture.infrastructure.system import (\n    AudioRecorder,\n    ProcessMonitor,",
    )
    anchor = "def cmd_process(args: argparse.Namespace) -> None:\n"
    record = '''def cmd_record(args: argparse.Namespace) -> None:\n    del args\n    import time\n\n    recorder = AudioRecorder()\n    path = recorder.start()\n    print(f"Recording: {path}")\n    print("Press Ctrl+C to stop.")\n    try:\n        while True:\n            time.sleep(0.25)\n    except KeyboardInterrupt:\n        pass\n    finally:\n        files = recorder.stop() if recorder.is_recording else None\n    if files:\n        for saved in files:\n            print(f"Saved: {saved}")\n\n\n'''
    handlers = Path(path)
    handler_text = handlers.read_text(encoding="utf-8")
    if "def cmd_record(" not in handler_text:
        if anchor not in handler_text:
            raise SystemExit("cmd_process anchor missing")
        handlers.write_text(handler_text.replace(anchor, record + anchor, 1), encoding="utf-8")
    replace(
        path,
        'GraphStorage(Path("data/graph.jsonl"))',
        'GraphStorage(runtime_directories().cache / "graph" / "graph.jsonl")',
    )
    replace(
        path,
        '    summary_dir = Path("data/summaries")\n    novel_dir = Path("data/novels")\n    evaluation_dir = summary_dir.parent / "evaluations"',
        '    summary_dir = settings.summary_dir\n    novel_dir = settings.novel_out_dir\n    evaluation_dir = runtime_directories().data / "evaluations"',
    )
    replace(
        path,
        '    transcript_dir = Path("data/transcripts")\n    summary_dir = Path("data/summaries")\n    recording_dir = Path("data/recordings")',
        '    transcript_dir = settings.transcript_dir\n    summary_dir = settings.summary_dir\n    recording_dir = settings.recording_dir',
    )

    path = "apps/capture-vrchat/src/vlog_capture/infrastructure/repositories.py"
    replace(path, "from dotenv import load_dotenv\n", "")
    replace(
        path,
        "from vlog_capture.infrastructure.settings import settings\n",
        "from vlog_capture.infrastructure.settings import settings\nfrom vlog_capture.portability import runtime_directories\n",
    )
    replace(
        path,
        '    def __init__(self, file_path: str = "data/tasks.json"):\n        self.file_path = Path(file_path)',
        '    def __init__(self, file_path: str | Path | None = None):\n        self.file_path = (\n            Path(file_path) if file_path is not None else runtime_directories().state / "tasks.json"\n        )',
    )
    replace(
        path,
        '    def __init__(self) -> None:\n        load_dotenv()\n        url = os.environ.get("SUPABASE_URL")\n        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")',
        '    def __init__(self) -> None:\n        url = settings.supabase_url\n        key = settings.supabase_service_role_key',
    )

    path = "apps/capture-vrchat/src/vlog_capture/infrastructure/strict_sync.py"
    replace(path, "from dotenv import load_dotenv\n", "")
    replace(
        path,
        "from vlog_capture.infrastructure.settings import settings\n\nload_dotenv()\n",
        "from vlog_capture.infrastructure.settings import settings\nfrom vlog_capture.portability import runtime_directories\n",
    )
    replace(
        path,
        '        url = os.environ.get("SUPABASE_URL")\n        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")',
        '        url = settings.supabase_url\n        key = settings.supabase_service_role_key',
    )
    replace(
        path,
        '        report_dir = Path("data/sync_reports")',
        '        report_dir = runtime_directories().state / "sync_reports"',
    )

    path = "apps/capture-vrchat/src/vlog_capture/infrastructure/audit_v2.py"
    replace(
        path,
        "from vlog_capture.domain.audit import AuditFinding, AuditReport, AuditState\n",
        "from vlog_capture.domain.audit import AuditFinding, AuditReport, AuditState\nfrom vlog_capture.portability import runtime_directories\n",
    )
    replace(
        path,
        '        run_id: str | None = None,\n        run_log: Path = Path("data/daily_runs.jsonl"),\n        trace_log: Path = Path("data/traces.jsonl"),\n    ) -> None:\n        self.run_id = run_id\n        self.run_log = run_log\n        self.trace_log = trace_log',
        '        run_id: str | None = None,\n        run_log: Path | None = None,\n        trace_log: Path | None = None,\n    ) -> None:\n        directories = runtime_directories()\n        self.run_id = run_id\n        self.run_log = run_log or directories.state / "daily_runs.jsonl"\n        self.trace_log = trace_log or directories.state / "traces.jsonl"',
    )
    replace(
        path,
        '        path = Path("data/sync_reports") / f"{run_id}.json"',
        '        path = runtime_directories().state / "sync_reports" / f"{run_id}.json"',
    )

    path = "scripts/check_runtime_contract.py"
    replace(
        path,
        "    for relative in paths or tracked_files():\n        if relative not in RUNTIME_FILES and not relative.startswith(RUNTIME_PREFIXES):",
        '    for relative in paths or tracked_files():\n        if relative == "scripts/check_runtime_contract.py":\n            continue\n        if relative not in RUNTIME_FILES and not relative.startswith(RUNTIME_PREFIXES):',
    )

    Path("scripts/open_operations.sh").write_text(
        '''#!/usr/bin/env bash\nset -euo pipefail\n\nROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"\ncd "$ROOT"\n\nDAYS="${1:-90}"\nuv run --frozen vlog-operations report --days "$DAYS" --open\n''',
        encoding="utf-8",
    )

    Path("scripts/update_image_urls.py").write_text(
        '''from pathlib import Path\n\nfrom supabase import create_client\nfrom vlog_capture.infrastructure.settings import settings\n\nif not settings.supabase_url or not settings.supabase_service_role_key:\n    raise RuntimeError("Supabase configuration is required")\n\nsupabase = create_client(settings.supabase_url, settings.supabase_service_role_key)\n\nphotos_dir = Path("apps/reader/public/photos")\ninfographics_dir = Path("apps/reader/public/infographics")\n\nfor photo in photos_dir.glob("*.png"):\n    date = photo.stem.replace(" copy", "")\n    if "_" in date:\n        continue\n    image_url = f"/photos/{photo.name}"\n    supabase.table("novels").update({"image_url": image_url}).eq("date", date).execute()\n    print(f"novels: {date} -> {image_url}")\n\nfor infographic in infographics_dir.glob("*_summary.png"):\n    date = infographic.stem.replace("_summary", "")\n    image_url = f"/infographics/{infographic.name}"\n    supabase.table("daily_entries").update({"image_url": image_url}).eq("date", date).execute()\n    print(f"daily_entries: {date} -> {image_url}")\n''',
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
