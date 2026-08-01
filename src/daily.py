from __future__ import annotations

import json
import os
import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable, Sequence
from uuid import uuid4

CommandRunner = Callable[[Sequence[str], dict[str, str], Path], None]


def _run_command(command: Sequence[str], env: dict[str, str], cwd: Path) -> None:
    subprocess.run(command, check=True, env=env, cwd=cwd)


def _vrchat_running() -> bool:
    from src.infrastructure.system import ProcessMonitor

    return ProcessMonitor().is_running()


class DailyPipeline:
    def __init__(
        self,
        runner: CommandRunner = _run_command,
        monitor: Callable[[], bool] = _vrchat_running,
        project_root: Path | None = None,
    ) -> None:
        self.runner = runner
        self.monitor = monitor
        self.project_root = (project_root or Path.cwd()).resolve()
        self.run_log = self.project_root / "data/daily_runs.jsonl"

    def run(self) -> str | None:
        if self.monitor():
            print("VRChat is running; daily processing skipped without success notice.")
            return None

        run_id = str(uuid4())
        env = dict(os.environ)
        env["VLOG_RUN_ID"] = run_id
        env["VLOG_DAILY_VERIFIED"] = "0"

        today = date.today()
        dates = [today - timedelta(days=1), today]
        for target in dates:
            date_str = target.strftime("%Y%m%d")
            for audio_path in self._recordings(date_str):
                transcript = Path("data/transcripts") / f"{audio_path.stem}.txt"
                self._stage(
                    run_id,
                    f"transcribe:{audio_path.stem}",
                    ["transcriber"],
                    [transcript],
                    env,
                    "transcribe",
                    "--file",
                    str(audio_path),
                )

        for target in dates:
            date_str = target.strftime("%Y%m%d")
            if self._has_transcript(date_str):
                summary = Path("data/summaries") / f"{date_str}_summary.txt"
                self._stage(
                    run_id,
                    f"summarize:{date_str}",
                    ["summarizer"],
                    [summary],
                    env,
                    "summarize",
                    "--date",
                    date_str,
                )
            summary = self.project_root / "data/summaries" / f"{date_str}_summary.txt"
            if self._nonempty(summary):
                self._stage(
                    run_id,
                    f"novel:{date_str}",
                    ["novelizer", "image_generator"],
                    [
                        Path("data/novels") / f"{date_str}.md",
                        Path("data/photos") / f"{date_str}.png",
                    ],
                    env,
                    "novel",
                    "--date",
                    date_str,
                )

        sync_report = Path("data/sync_reports") / f"{run_id}.json"
        self._stage(
            run_id,
            "sync",
            ["supabase"],
            [sync_report],
            env,
            "sync",
        )

        self._cli(env, "audit", "--strict", "--run-id", run_id)
        env["VLOG_DAILY_VERIFIED"] = "1"
        self._cli(
            env,
            "notify",
            "--message",
            "✅ 日次処理と証跡監査が完了しました。\n"
            f"run_id: {run_id}\n"
            "🌐 Reader: https://kaflog.vercel.app",
        )
        return run_id

    def _stage(
        self,
        run_id: str,
        task_name: str,
        components: list[str],
        artifacts: list[Path],
        env: dict[str, str],
        *command_args: str,
    ) -> None:
        stage_env = dict(env)
        stage_env["VLOG_TASK_NAME"] = task_name
        self._log(
            {
                "timestamp": datetime.now().isoformat(),
                "run_id": run_id,
                "task_name": task_name,
                "status": "try",
                "expected_components": components,
            }
        )
        try:
            self._cli(stage_env, *command_args)
            artifact_states = {
                str(path): self._nonempty(self.project_root / path)
                for path in artifacts
            }
            if not all(artifact_states.values()):
                missing = [path for path, ok in artifact_states.items() if not ok]
                raise RuntimeError("Missing stage artifacts: " + ", ".join(missing))
            self._log(
                {
                    "timestamp": datetime.now().isoformat(),
                    "run_id": run_id,
                    "task_name": task_name,
                    "status": "success",
                    "expected_components": components,
                    "completed_components": components,
                    "verification": {
                        "verified": True,
                        "artifacts": artifact_states,
                    },
                }
            )
        except Exception as exc:
            self._log(
                {
                    "timestamp": datetime.now().isoformat(),
                    "run_id": run_id,
                    "task_name": task_name,
                    "status": "failed",
                    "expected_components": components,
                    "error": str(exc),
                }
            )
            raise

    def _cli(self, env: dict[str, str], *args: str) -> None:
        self.runner(
            ["uv", "run", "python", "-m", "src.cli", *args],
            env,
            self.project_root,
        )

    def _recordings(self, date_str: str) -> list[Path]:
        recording_dir = self.project_root / "data/recordings"
        return sorted(
            path
            for suffix in ("wav", "flac", "mp3")
            for path in recording_dir.glob(f"{date_str}*.{suffix}")
        )

    def _has_transcript(self, date_str: str) -> bool:
        transcript_dir = self.project_root / "data/transcripts"
        return any(
            self._nonempty(path) for path in transcript_dir.glob(f"*{date_str}*.txt")
        )

    @staticmethod
    def _nonempty(path: Path) -> bool:
        return path.is_file() and path.stat().st_size > 0

    def _log(self, payload: dict[str, object]) -> None:
        self.run_log.parent.mkdir(parents=True, exist_ok=True)
        with self.run_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def main() -> None:
    DailyPipeline().run()


if __name__ == "__main__":
    main()
