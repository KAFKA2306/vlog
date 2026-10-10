import json
import re
import subprocess
import sys
from pathlib import Path

SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
PRODUCTION_REF = "main"


def identity_failures(
    payload: dict[str, object],
    expected_sha: str | None = None,
    expected_ref: str = PRODUCTION_REF,
) -> list[str]:
    failures = []
    if payload.get("status") != "ok":
        failures.append("status is not ok")
    if payload.get("environment") != "production":
        failures.append("environment is not production")
    if not str(payload.get("deploymentId") or "").startswith("dpl_"):
        failures.append("deploymentId is missing or not dpl_*")
    sha = payload.get("gitCommitSha")
    if not isinstance(sha, str) or not SHA_PATTERN.fullmatch(sha):
        failures.append("gitCommitSha is missing or not a full 40-hex SHA")
    elif expected_sha is not None and sha != expected_sha:
        failures.append(f"gitCommitSha {sha} != expected {expected_sha}")
    if payload.get("gitCommitRef") != expected_ref:
        failures.append(f"gitCommitRef is not {expected_ref}")
    return failures


def main(health_json: str, repo: str) -> int:
    payload = json.loads(Path(health_json).read_text(encoding="utf-8"))
    failures = identity_failures(payload)
    if not failures:
        target = f"{payload['gitCommitSha']}^{{commit}}"
        resolved = subprocess.run(
            ["git", "-C", repo, "cat-file", "-e", target], capture_output=True
        )
        if resolved.returncode != 0:
            failures.append("gitCommitSha does not resolve to a repository commit")
    for failure in failures:
        print(f"FAIL: {failure}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
