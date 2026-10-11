#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from datetime import date
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict

REPO_ROOT = Path(__file__).resolve().parents[1]
STAR_PATH = "schemas/ledger/star.yaml"
HEADER = "<!-- GENERATED from schemas/ledger/star.yaml by scripts/generate_ledger.py. Do not edit. -->"
FOOTER = "<!-- /GENERATED -->"


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class DimDate(Frozen):
    date: date
    label: str


class DimStatus(Frozen):
    name: str
    meaning: str


class DimDoc(Frozen):
    path: str
    authority_class: str
    owner: str
    authority: str


class FactDecision(Frozen):
    adr: str
    file: str
    decision: str
    status: str
    audit_status: str
    audited_on: date


class FactVerification(Frozen):
    task: str
    covers: str
    evidence_level: str


class Star(Frozen):
    dim_date: tuple[DimDate, ...]
    dim_status: tuple[DimStatus, ...]
    dim_doc: tuple[DimDoc, ...]
    fact_decision: tuple[FactDecision, ...]
    fact_verification: tuple[FactVerification, ...]


def load_star(root: Path) -> Star:
    raw = yaml.safe_load((root / STAR_PATH).read_text(encoding="utf-8"))
    return Star.model_validate(raw)


def _table(header: tuple[str, ...], rows: list[tuple[str, ...]]) -> str:
    lines = [
        "| " + " | ".join(header) + " |",
        "|" + "---|" * len(header),
        *("| " + " | ".join(row) + " |" for row in rows),
    ]
    return "\n".join(lines)


def adr_index(star: Star) -> str:
    return _table(
        ("ADR", "Decision", "Audit status"),
        [
            (f"[{d.adr}]({d.file})", d.decision, d.audit_status)
            for d in star.fact_decision
        ],
    )


def _doc_link(path: str) -> str:
    link = os.path.relpath(path, "docs")
    return f"[`{link}`]({link})" if not path.endswith("/") else f"[`{link}/`]({link}/)"


def source_of_truth_map(star: Star) -> str:
    return _table(
        ("Document", "Authority"),
        [(_doc_link(d.path), d.authority) for d in star.dim_doc],
    )


def decisions_ledger(star: Star) -> str:
    table = _table(
        ("ADR", "Status", "Audit status", "Audited on"),
        [
            (
                f"[{d.adr}](../adr/{d.file})",
                d.status,
                d.audit_status,
                d.audited_on.isoformat(),
            )
            for d in star.fact_decision
        ],
    )
    return (
        f"{HEADER}\n# Decision ledger\n\nOne row per ADR state. "
        f"Edit `{STAR_PATH}`, then run `task ledger:generate`.\n\n{table}\n"
    )


def verifications_ledger(star: Star) -> str:
    table = _table(
        ("Task", "Covers", "Evidence level on pass"),
        [
            (f"`task {v.task}`", v.covers, v.evidence_level)
            for v in star.fact_verification
        ],
    )
    return (
        f"{HEADER}\n# Verification ledger\n\nChecks and the strongest evidence level "
        "a pass can establish. Results are not recorded here; see CI and "
        f"environment evidence.\n\n{table}\n"
    )


def _embed(text: str, block: str) -> str:
    start = text.index(HEADER)
    end = text.index(FOOTER, start)
    return text[:start] + HEADER + "\n" + block + "\n" + text[end:]


def generate(root: Path) -> dict[str, str]:
    star = load_star(root)

    def read(relative: str) -> str:
        return (root / relative).read_text(encoding="utf-8")

    return {
        "docs/adr/README.md": _embed(read("docs/adr/README.md"), adr_index(star)),
        "docs/README.md": _embed(read("docs/README.md"), source_of_truth_map(star)),
        "docs/ledger/decisions.md": decisions_ledger(star),
        "docs/ledger/verifications.md": verifications_ledger(star),
    }


def write(rendered: dict[str, str], out: Path) -> None:
    for relative, text in rendered.items():
        target = out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate ledger views from the star schema."
    )
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    write(generate(root), (args.out or root).expanduser().resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
