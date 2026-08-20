#!/usr/bin/env python3
"""Deploy the Reader to the canonical KafLog Vercel project with provenance."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
READER = ROOT / "apps" / "reader"
DEFAULT_PROJECT_ID = "prj_t52LlD6qx3zdzdgOqBomZBfzzwb6"
DEFAULT_TEAM_ID = "team_WAiNUdK4pWv6eK8LxnaVY1mC"
DEFAULT_HEALTH_URL = "https://kaflog.vercel.app/api/health"


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def release_identity() -> tuple[str, str]:
    dirty = git("status", "--porcelain", "--untracked-files=all")
    if dirty:
        raise RuntimeError("production deploy requires a clean Git working tree")
    ref = git("branch", "--show-current")
    if ref != "main":
        raise RuntimeError(f"production deploy requires branch main, got {ref!r}")
    sha = git("rev-parse", "HEAD")
    if len(sha) != 40:
        raise RuntimeError(f"unexpected Git SHA: {sha!r}")
    return sha, ref


def deploy(sha: str, ref: str) -> None:
    env = dict(os.environ)
    env.setdefault("VERCEL_PROJECT_ID", DEFAULT_PROJECT_ID)
    env.setdefault("VERCEL_ORG_ID", DEFAULT_TEAM_ID)
    command = [
        "bunx",
        "vercel",
        "deploy",
        "--prod",
        "--yes",
        "--cwd",
        str(READER),
        "--project",
        env["VERCEL_PROJECT_ID"],
        "--env",
        f"VLOG_DEPLOY_GIT_SHA={sha}",
        "--env",
        f"VLOG_DEPLOY_GIT_REF={ref}",
        "--meta",
        f"gitCommitSha={sha}",
        "--meta",
        f"gitCommitRef={ref}",
    ]
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def health(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=15) as response:  # noqa: S310
        if not 200 <= response.status < 300:
            raise RuntimeError(f"health endpoint returned HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))


def verify_production(sha: str, ref: str, url: str, attempts: int = 12) -> None:
    last: dict[str, object] | None = None
    for _ in range(attempts):
        try:
            last = health(url)
        except (OSError, ValueError, json.JSONDecodeError):
            last = None
        if (
            last
            and last.get("status") == "ok"
            and last.get("environment") == "production"
            and last.get("gitCommitSha") == sha
            and last.get("gitCommitRef") == ref
            and str(last.get("deploymentId") or "").startswith("dpl_")
        ):
            print(json.dumps(last, ensure_ascii=False, indent=2))
            return
        time.sleep(5)
    raise RuntimeError(
        f"production health did not converge to sha={sha} ref={ref}; last={last}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--health-url", default=DEFAULT_HEALTH_URL)
    parser.add_argument("--verify-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        sha, ref = release_identity()
        if not args.verify_only:
            deploy(sha, ref)
        verify_production(sha, ref, args.health_url)
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"deploy-reader: FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
