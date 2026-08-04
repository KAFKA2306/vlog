from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_batch() -> bool:
    print("Starting a new batch processing...")
    env = os.environ.copy()
    env["COGNEE_SKIP_CONNECTION_TEST"] = "true"
    result = subprocess.run(
        ["uv", "run", "--extra", "cognee", "python", "scripts/ingest_to_cognee.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    print(result.stdout)
    if result.stderr:
        print(f"Error: {result.stderr}")
    return result.returncode == 0 and "No pending files." not in result.stdout


def main() -> None:
    while run_batch():
        print("Batch complete. Waiting 15 seconds before the next batch...")
        time.sleep(15)
    print("All pending files have been processed or no further progress was made.")


if __name__ == "__main__":
    main()
