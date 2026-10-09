import argparse
import json
import os
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path

import yaml

ENDPOINT = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5:7b"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_PATH = PROJECT_ROOT / "data/prompts.yaml"
MAX_CHARS = 12000
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
DRAFT_HEADER = (
    "> 非公開の下書きです。ローカル生成（外部送信なし）。公開前に人の確認が必要です。"
)


def require_local_endpoint(url: str) -> None:
    host = urllib.parse.urlparse(url).hostname or ""
    if host not in LOOPBACK_HOSTS:
        raise ValueError(f"generation endpoint must be loopback, got {host!r}")


def load_template() -> str:
    prompts = yaml.safe_load(PROMPTS_PATH.read_text(encoding="utf-8"))
    return prompts["summarizer"]["template"]


def private_output_dir() -> Path:
    return PROJECT_ROOT / "data/private/nikki"


def build_transcript(records: list[dict]) -> str:
    lines: list[str] = []
    for record in records:
        kind = record.get("t")
        if kind == "heard":
            lines.append(f"あなた: {record.get('text', '')}")
        elif kind == "said":
            lines.append(f"ムチォ: {' '.join(record.get('lines', []))}")
        elif kind == "event":
            lines.append(f"［{record.get('name', '')}］")
    return "\n".join(lines)


def build_transcript_capped(
    records: list[dict], limit: int = MAX_CHARS
) -> tuple[str, bool]:
    text = build_transcript(records)
    if len(text) <= limit:
        return text, False
    return text[:limit], True


def ollama_generate(prompt: str) -> str:
    require_local_endpoint(ENDPOINT)
    body = json.dumps(
        {
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_ctx": 8192},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=600) as response:
        return json.loads(response.read().decode("utf-8"))["response"].strip()


def _load_records(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def generate_days(
    logs_dir: Path,
    out_dir: Path,
    generate: Callable[[str], str] = ollama_generate,
    only: str | None = None,
) -> list[str]:
    template = load_template()
    out_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    written: list[str] = []
    for path in sorted(logs_dir.glob("*.jsonl")):
        day = path.stem
        if only is not None and day != only:
            continue
        target = out_dir / f"{day}.md"
        if target.exists():
            continue
        transcript, truncated = build_transcript_capped(_load_records(path))
        if not transcript:
            continue
        prompt = template.format(date=day, transcript=transcript)
        summary = generate(prompt)
        note = "\n> 入力は上限で切り詰めました。" if truncated else ""
        target.write_text(
            f"# {day}\n\n{DRAFT_HEADER}{note}\n\n{summary}\n", encoding="utf-8"
        )
        os.chmod(target, 0o600)
        written.append(day)
    return written


def _main() -> None:
    parser = argparse.ArgumentParser(
        description="Local-only nikki drafts from VRCPet logs"
    )
    parser.add_argument("--logs", type=Path, required=True)
    parser.add_argument("--date", default=None)
    args = parser.parse_args()
    written = generate_days(args.logs, private_output_dir(), only=args.date)
    print(f"drafts_written={len(written)} out={private_output_dir()}")


if __name__ == "__main__":
    _main()
