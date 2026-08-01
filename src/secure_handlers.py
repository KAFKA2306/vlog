from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from src.domain.audit import AuditState
from src.infrastructure.audit_v2 import StrictRunAuditor
from src.infrastructure.strict_sync import StrictSupabaseSync


def cmd_sync(args: argparse.Namespace) -> None:
    report = StrictSupabaseSync().sync()
    print(json.dumps(report.to_dict(), ensure_ascii=False))


def cmd_novel(args: argparse.Namespace) -> None:
    from src.infrastructure.ai import ImageGenerator, Novelizer
    from src.infrastructure.graph_storage import GraphStorage
    from src.infrastructure.settings import settings
    from src.use_cases.build_novel import BuildNovelUseCase

    graph_storage = GraphStorage(Path("data/graph.jsonl"))
    BuildNovelUseCase(Novelizer(), ImageGenerator(), graph_storage).execute(args.date)
    artifacts = [
        Path(settings.novel_out_dir) / f"{args.date}.md",
        Path(settings.photo_dir) / f"{args.date}.png",
    ]
    missing = [str(path) for path in artifacts if not _nonempty(path)]
    if missing:
        raise RuntimeError("Novel stage artifacts are missing: " + ", ".join(missing))


def cmd_audit(args: argparse.Namespace) -> None:
    report = StrictRunAuditor(run_id=getattr(args, "run_id", None)).run()
    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_report(report)
    if args.strict and report.has_blockers:
        sys.exit(1)


def cmd_notify(args: argparse.Namespace) -> None:
    if (
        args.message.startswith("✅ 日次処理")
        and os.environ.get("VLOG_DAILY_VERIFIED") != "1"
    ):
        raise RuntimeError("Daily success notification requires a verified run")
    from src.infrastructure.discord import DiscordClient

    DiscordClient().send_message(args.message)


def _nonempty(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0


def _print_report(report: Any) -> None:
    counts = {state: 0 for state in AuditState}
    for finding in report.findings:
        counts[finding.state] += 1
        details = f" | {finding.details}" if finding.details else ""
        print(
            f"{finding.state.value.upper():13} {finding.check_name} :: "
            f"{finding.evidence}{details}"
        )
    print(
        "SUMMARY        "
        f"pass={counts[AuditState.PASS]} "
        f"fail={counts[AuditState.FAIL]} "
        f"unverified={counts[AuditState.UNVERIFIED]} "
        f"n/a={counts[AuditState.NOT_APPLICABLE]}"
    )
