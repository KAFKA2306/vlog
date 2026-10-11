import shutil
from pathlib import Path

import yaml

from scripts.check_repository_boundaries import check_generated_ledgers
from scripts.generate_ledger import HEADER, generate, load_star

ROOT = Path(__file__).resolve().parents[1]
GENERATED = (
    "docs/adr/README.md",
    "docs/README.md",
    "docs/ledger/decisions.md",
    "docs/ledger/verifications.md",
)


def _copy_inputs(target: Path) -> None:
    for relative in (
        "schemas/ledger/star.yaml",
        "Taskfile.yaml",
        "docs/markdown-governance.md",
        *GENERATED,
    ):
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / relative, destination)
    shutil.copytree(ROOT / "docs/adr", target / "docs/adr", dirs_exist_ok=True)


def test_generation_is_deterministic() -> None:
    assert generate(ROOT) == generate(ROOT)


def test_generated_files_carry_header_and_match_checked_in() -> None:
    rendered = generate(ROOT)
    assert set(rendered) == set(GENERATED)
    for relative, text in rendered.items():
        assert HEADER in text.splitlines()
        assert (ROOT / relative).read_text(encoding="utf-8") == text
    for relative in ("docs/ledger/decisions.md", "docs/ledger/verifications.md"):
        assert rendered[relative].startswith(HEADER + "\n")


def test_stale_generated_file_is_detected(tmp_path: Path) -> None:
    _copy_inputs(tmp_path)
    assert check_generated_ledgers(tmp_path) == []
    stale = tmp_path / "docs/ledger/decisions.md"
    stale.write_text(stale.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")
    codes = {violation.code for violation in check_generated_ledgers(tmp_path)}
    assert codes == {"stale-generated-ledger"}


def test_check_does_not_write_into_repository(tmp_path: Path) -> None:
    _copy_inputs(tmp_path)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    check_generated_ledgers(tmp_path)
    assert before == sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))


def test_no_private_data_or_issue_state_in_schema() -> None:
    raw = (ROOT / "schemas/ledger/star.yaml").read_text(encoding="utf-8")
    assert "data/" not in raw
    assert "fact_issue" not in raw
    assert set(yaml.safe_load(raw)) == {
        "dim_date",
        "dim_doc",
        "dim_status",
        "fact_decision",
        "fact_verification",
    }


def test_star_references_resolve() -> None:
    star = load_star(ROOT)
    taskfile = (ROOT / "Taskfile.yaml").read_text(encoding="utf-8")
    governance = (ROOT / "docs/markdown-governance.md").read_text(encoding="utf-8")
    dates = {row.date for row in star.dim_date}
    statuses = {row.name for row in star.dim_status}
    for decision in star.fact_decision:
        assert (ROOT / "docs/adr" / decision.file).is_file()
        assert decision.audited_on in dates
    for check in star.fact_verification:
        assert check.evidence_level in statuses
        assert f"\n  {check.task}:" in taskfile
    for doc in star.dim_doc:
        assert (ROOT / doc.path).exists()
        row = next(
            line
            for line in governance.splitlines()
            if line.startswith(f"| {doc.authority_class} |")
        )
        assert f"`{doc.owner}`" in row
