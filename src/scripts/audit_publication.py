from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta

from src.infrastructure.publication import is_publishable_summary
from src.infrastructure.settings import settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=92)
    args = parser.parse_args()

    since = date.today() - timedelta(days=args.days)
    publishable: list[str] = []
    blocked: list[str] = []
    for path in sorted(settings.summary_dir.glob("*_summary.txt")):
        date_str = path.stem.removesuffix("_summary")
        if not date_str.isdigit() or len(date_str) != 8:
            continue
        if datetime.strptime(date_str, "%Y%m%d").date() < since:
            continue
        (publishable if is_publishable_summary(date_str) else blocked).append(date_str)

    print(f"window={since.isoformat()}..{date.today().isoformat()}")
    print(f"publishable={len(publishable)} blocked={len(blocked)}")
    for date_str in blocked:
        print(f"BLOCKED {date_str}")


if __name__ == "__main__":
    main()
