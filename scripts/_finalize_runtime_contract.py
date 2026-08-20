#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_required(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"required pattern not found for {label}")
    return text.replace(old, new)


def patch_operations() -> None:
    path = ROOT / "apps/capture-vrchat/src/vlog_capture/operations.py"
    text = path.read_text(encoding="utf-8")
    text = replace_required(
        text,
        "    sanitize,\n)\n\nCATEGORY_ORDER",
        "    sanitize,\n)\nfrom vlog_capture.portability import runtime_directories\n\nCATEGORY_ORDER",
        "operations runtime import",
    )
    text = replace_required(
        text,
        "class OperationsLoader:\n    def __init__(self, root: Path = Path.cwd()) -> None:\n        self.root = root.resolve()",
        'class OperationsLoader:\n    def __init__(self, root: Path | None = None) -> None:\n        # Explicit roots preserve the legacy test/import layout; production uses state home.\n        self.root = (\n            (root / "data") if root is not None else runtime_directories().state\n        ).resolve()',
        "operations loader root",
    )
    replacements = {
        'self.root / "data/error_events.jsonl"': 'self.root / "error_events.jsonl"',
        'self.root / "data/incidents.jsonl"': 'self.root / "incidents.jsonl"',
        'self.root / "data/daily_runs.jsonl"': 'self.root / "daily_runs.jsonl"',
        'self.root / "data/logs/vlog.log"': 'self.root / "logs/vlog.log"',
        'log = OperationalEventLog(root / "data/error_events.jsonl")': 'state_root = runtime_directories().state\n    log = OperationalEventLog(state_root / "error_events.jsonl")',
        '"uv run python -m src.daily" in daily_text': '"uv run --frozen vlog-daily" in daily_text',
        'OperationalEventLog(root / "data/error_events.jsonl").emit(': 'OperationalEventLog(runtime_directories().state / "error_events.jsonl").emit(',
        'default="data/reports/operations.html"': 'default="reports/operations.html"',
        'default="data/reports/operations.json"': 'default="reports/operations.json"',
        '"data/reports/operations.html"': '"reports/operations.html"',
        '"data/reports/operations.json"': '"reports/operations.json"',
    }
    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new)

    old_writable = """        (
            "project data writable",
            os.access(root / "data", os.W_OK)
            if (root / "data").exists()
            else os.access(root, os.W_OK),
            str(root / "data"),
        ),"""
    new_writable = """        (
            "runtime state writable",
            os.access(state_root, os.W_OK)
            if state_root.exists()
            else os.access(state_root.parent, os.W_OK),
            str(state_root),
        ),"""
    text = replace_required(text, old_writable, new_writable, "doctor writable path")

    old_keys = """    for key in ("GOOGLE_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"):
        checks.append(
            (
                key,
                bool(os.environ.get(key)),
                "configured" if os.environ.get(key) else "missing",
            )
        )"""
    new_keys = """    for canonical, fallback in (
        ("VLOG_GEMINI_API_KEY", "GOOGLE_API_KEY"),
        ("VLOG_SUPABASE_URL", "SUPABASE_URL"),
        ("VLOG_SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SERVICE_ROLE_KEY"),
    ):
        configured = bool(os.environ.get(canonical) or os.environ.get(fallback))
        checks.append(
            (canonical, configured, "configured" if configured else "missing")
        )"""
    text = replace_required(text, old_keys, new_keys, "doctor config aliases")

    old_main = """    root = Path.cwd()
    report = build_report(OperationsLoader(root).load(args.days), args.days)
    html_path, json_path = root / args.html, root / args.json"""
    new_main = """    state_root = runtime_directories().state
    report = build_report(OperationsLoader().load(args.days), args.days)
    html_arg, json_arg = Path(args.html), Path(args.json)
    html_path = html_arg if html_arg.is_absolute() else state_root / html_arg
    json_path = json_arg if json_arg.is_absolute() else state_root / json_arg"""
    text = replace_required(text, old_main, new_main, "operations report root")
    path.write_text(text, encoding="utf-8")


def patch_taskfile() -> None:
    path = ROOT / "Taskfile.yaml"
    text = path.read_text(encoding="utf-8")
    text = replace_required(text, 'version: "3"', 'version: "3.52.0"', "Task version")
    text = replace_required(
        text,
        """env:
  UV: "uv"
  BUN: "bun"
  BUNX: "bunx"

tasks:""",
        """env:
  UV: "uv"
  BUN: "bun"
  BUNX: "bunx"

vars:
  VLOG_DATA_HOME:
    sh: $UV run --frozen python -c "from vlog_capture.portability import runtime_directories; print(runtime_directories().data)"
  VLOG_STATE_HOME:
    sh: $UV run --frozen python -c "from vlog_capture.portability import runtime_directories; print(runtime_directories().state)"

tasks:""",
        "Task runtime vars",
    )
    old_status = """  status:
    desc: Windows・systemd・日次タイマー・ログの状態確認
    cmds:
      - powershell.exe -NoProfile -Command "Get-ScheduledTask -TaskName VlogAutoDiary | Select-Object TaskName,State | Format-Table -AutoSize"
      - systemctl --user show vlog.service vlog-daily.timer -p Id -p LoadState -p ActiveState -p SubState -p UnitFileState
      - systemctl --user list-timers vlog-daily.timer --all --no-pager
      - journalctl --user -u vlog.service -u vlog-daily.service --no-pager -n 20
"""
    new_status = """  status:
    desc: 現在platformのVLog supervisor状態確認
    cmds:
      - task: status:windows
      - task: status:linux

  status:windows:
    desc: Windows Task Scheduler状態
    platforms: [windows]
    cmd: powershell.exe -NoProfile -Command "Get-ScheduledTask -TaskName VlogAutoDiary | Select-Object TaskName,State | Format-Table -AutoSize"

  status:linux:
    desc: systemd・日次タイマー・ログ状態
    platforms: [linux]
    cmds:
      - systemctl --user show vlog.service vlog-daily.timer -p Id -p LoadState -p ActiveState -p SubState -p UnitFileState
      - systemctl --user list-timers vlog-daily.timer --all --no-pager
      - journalctl --user -u vlog.service -u vlog-daily.service --no-pager -n 20
"""
    text = replace_required(text, old_status, new_status, "platform status tasks")

    text = text.replace("data/recordings/", '"{{.VLOG_DATA_HOME}}"/recordings/')
    text = text.replace(
        "touch data/summaries/*.txt", 'touch "{{.VLOG_DATA_HOME}}"/summaries/*.txt'
    )
    text = text.replace("$UV run vlog", "$UV run --frozen vlog")
    text = text.replace("$UV run python", "$UV run --frozen python")
    text = text.replace("$UV run pytest", "$UV run --frozen pytest")
    text = text.replace("$UV run ruff", "$UV run --frozen ruff")
    text = text.replace("$UV run ty", "$UV run --frozen ty")

    old_deploy = """  web:deploy:
    desc: Vercelデプロイ
    deps: [web:build]
    cmds:
      - cd apps/reader && $BUNX vercel link --project kaflog --yes
      - cd apps/reader && $BUNX vercel --prod --yes
"""
    new_deploy = """  web:deploy:
    desc: clean mainをGit provenance付きでKafLog productionへdeploy
    deps: [web:build]
    cmd: $UV run --frozen python scripts/deploy_reader.py
"""
    text = replace_required(text, old_deploy, new_deploy, "Vercel deploy task")

    old_env = """  web:env:
    desc: 環境変数抽出
    cmds:
      - test -f .env || (echo ".env がありません" && exit 1)
      - |
        . ./.env
        cat >apps/reader/.env.local <<EOF
        NEXT_PUBLIC_SUPABASE_URL=${NEXT_PUBLIC_SUPABASE_URL}
        NEXT_PUBLIC_SUPABASE_ANON_KEY=${NEXT_PUBLIC_SUPABASE_ANON_KEY}
        EOF
"""
    new_env = """  web:env:
    desc: process environmentからReader開発envを生成
    cmd: $UV run --frozen python scripts/write_reader_env.py
"""
    text = replace_required(text, old_env, new_env, "Reader env task")

    text = text.replace(
        "cmd: cd apps/reader && $BUN ci",
        "cmd: cd apps/reader && $BUN install --frozen-lockfile",
    )
    text = text.replace(
        'python3 infra/systemd/render.py --root "$(pwd)"',
        '$UV run --frozen python infra/systemd/render.py --root "{{.ROOT_DIR}}"',
    )
    text = text.replace("$UV run --frozen --frozen", "$UV run --frozen")
    path.write_text(text, encoding="utf-8")


def main() -> None:
    patch_operations()
    patch_taskfile()

    taskfile = (ROOT / "Taskfile.yaml").read_text(encoding="utf-8")
    forbidden = ("USER_WORKING_DIR", ". ./.env", "vercel link --project kaflog")
    remaining = [token for token in forbidden if token in taskfile]
    if remaining:
        raise RuntimeError(
            "Taskfile finalization left forbidden tokens: " + ", ".join(remaining)
        )


if __name__ == "__main__":
    main()
