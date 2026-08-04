from __future__ import annotations

import hashlib
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", ".venv", "node_modules", ".next"}
OLD_PATTERNS = {
    "legacy_root_src": re.compile(r"(?<!apps/capture-vrchat/)\bsrc/"),
    "legacy_frontend_reader": re.compile(r"frontend/reader"),
    "legacy_root_windows": re.compile(r"(?<!infra/)\bwindows/"),
    "legacy_root_supabase": re.compile(r"(?<!infra/)\bsupabase/"),
    "absolute_file_uri": re.compile(r"file://"),
    "absolute_home": re.compile(r"/home/[A-Za-z0-9_.-]+/"),
    "windows_drive_path": re.compile(r"[A-Za-z]:\\\\"),
    "completion_claim": re.compile(r"(?:完全|すべて|100%|production verified|本番.*確認済み)", re.IGNORECASE),
}
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def markdown_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".md", ".markdown"}:
            continue
        if any(part in EXCLUDED_PARTS for part in path.relative_to(ROOT).parts):
            continue
        files.append(path)
    return sorted(files)


def strip_code_fences(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def normalized_body(text: str) -> str:
    text = strip_code_fences(text)
    lines = []
    for line in text.splitlines():
        line = line.strip().lower()
        if not line or line.startswith("#") or line.startswith("---"):
            continue
        line = re.sub(r"https?://\S+", "<url>", line)
        line = re.sub(r"\s+", " ", line)
        lines.append(line)
    return "\n".join(lines)


def resolve_relative_link(source: Path, raw_target: str) -> str | None:
    target = raw_target.strip().split("#", 1)[0].split("?", 1)[0]
    if not target or target.startswith(("http://", "https://", "mailto:", "tel:", "#")):
        return None
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    candidate = (source.parent / target).resolve()
    try:
        candidate.relative_to(ROOT)
    except ValueError:
        return f"outside repository: {raw_target}"
    if not candidate.exists():
        return f"missing: {raw_target}"
    return None


def main() -> None:
    files = markdown_files()
    records: list[dict[str, object]] = []
    normalized: dict[str, str] = {}

    for path in files:
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT).as_posix()
        heading_match = HEADING_RE.search(text)
        broken_links = []
        for raw_target in LINK_RE.findall(strip_code_fences(text)):
            failure = resolve_relative_link(path, raw_target)
            if failure:
                broken_links.append(failure)
        findings = {
            name: [index + 1 for index, line in enumerate(text.splitlines()) if pattern.search(line)]
            for name, pattern in OLD_PATTERNS.items()
        }
        findings = {name: lines for name, lines in findings.items() if lines}
        body = normalized_body(text)
        normalized[relative] = body
        records.append(
            {
                "path": relative,
                "lines": len(text.splitlines()),
                "bytes": len(text.encode("utf-8")),
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "title": heading_match.group(1).strip() if heading_match else None,
                "broken_links": broken_links,
                "findings": findings,
            }
        )

    duplicate_candidates = []
    paths = sorted(normalized)
    for index, left in enumerate(paths):
        if len(normalized[left]) < 200:
            continue
        for right in paths[index + 1 :]:
            if len(normalized[right]) < 200:
                continue
            ratio = SequenceMatcher(None, normalized[left], normalized[right]).ratio()
            if ratio >= 0.55:
                duplicate_candidates.append({"left": left, "right": right, "similarity": round(ratio, 3)})

    result = {
        "markdown_count": len(records),
        "total_lines": sum(int(record["lines"]) for record in records),
        "files": records,
        "duplicate_candidates": sorted(duplicate_candidates, key=lambda item: item["similarity"], reverse=True),
    }
    output_dir = ROOT / "artifacts"
    output_dir.mkdir(exist_ok=True)
    (output_dir / "markdown-audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Markdown files: {result['markdown_count']}")
    print(f"Total lines: {result['total_lines']}")
    print("\nFILES")
    for record in records:
        flags = []
        if record["broken_links"]:
            flags.append(f"broken_links={len(record['broken_links'])}")
        if record["findings"]:
            flags.append("findings=" + ",".join(record["findings"].keys()))
        suffix = f" [{' '.join(flags)}]" if flags else ""
        print(f"{record['path']}\t{record['lines']}\t{record['title'] or '(no H1)'}{suffix}")
    print("\nBROKEN LINKS")
    for record in records:
        for failure in record["broken_links"]:
            print(f"{record['path']}: {failure}")
    print("\nDUPLICATE CANDIDATES")
    for pair in result["duplicate_candidates"]:
        print(f"{pair['similarity']:.3f}\t{pair['left']}\t{pair['right']}")


if __name__ == "__main__":
    main()
