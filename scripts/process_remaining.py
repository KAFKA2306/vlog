import subprocess
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def run_batch():
    print("Starting a new batch processing...")
    import os
    env = os.environ.copy()
    env["COGNEE_SKIP_CONNECTION_TEST"] = "true"
    
    result = subprocess.run(
        ["uv", "run", "python", "scripts/ingest_to_cognee.py"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env=env
    )
    print(result.stdout)
    if result.stderr:
        print(f"Error: {result.stderr}")
    return result.returncode == 0 and "No pending files." not in result.stdout

def main():
    while True:
        has_more = run_batch()
        if not has_more:
            print("All pending files have been processed or no more progress can be made.")
            break
        print("Batch complete. Waiting 15 seconds before next batch to be safe...")
        time.sleep(15)

if __name__ == "__main__":
    main()
