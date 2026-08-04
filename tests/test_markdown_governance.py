from pathlib import Path

from scripts.check_repository_boundaries import _local_link_failure, check_markdown


def test_local_markdown_link_accepts_existing_target(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    source = docs / "README.md"
    target = docs / "guide.md"
    source.write_text("# Index\n", encoding="utf-8")
    target.write_text("# Guide\n", encoding="utf-8")

    assert _local_link_failure(tmp_path, source, "guide.md") is None


def test_local_markdown_link_rejects_missing_target(tmp_path: Path) -> None:
    source = tmp_path / "README.md"
    source.write_text("# Index\n", encoding="utf-8")

    assert (
        _local_link_failure(tmp_path, source, "missing.md")
        == "link target is missing: missing.md"
    )


def test_markdown_governance_rejects_nonportable_and_broken_links(
    tmp_path: Path,
) -> None:
    path = tmp_path / "README.md"
    path.write_text(
        "# Index\n\n[missing](missing.md)\n\n/home/example/private\n",
        encoding="utf-8",
    )

    violations = check_markdown(tmp_path, ["README.md"])
    codes = {violation.code for violation in violations}

    assert "broken-markdown-link" in codes
    assert "non-portable-markdown" in codes
