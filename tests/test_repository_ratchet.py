from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_canonical_memory_flow_is_single_documented_line() -> None:
    architecture = (ROOT / "docs/architecture/human-memory-v2.md").read_text(encoding="utf-8")
    assert "Evidence -> Human Memory -> Narrative Artifact -> Public Projection" in architecture
    assert "Private object storage" in architecture
    assert "PostgreSQL/Supabase" in architecture
    assert "Graphiti, Cognee, pgvector, and Qdrant are rebuildable projections" in architecture


def test_privacy_boundary_is_directly_enforced_by_ci() -> None:
    workflow = (ROOT / ".github/workflows/test.yml").read_text(encoding="utf-8")
    assert "scripts/check_repository_boundaries.py" in workflow
    assert "Enforce public/private repository boundaries" in workflow


def test_product_repository_has_no_independent_weekly_research_writer() -> None:
    assert not (ROOT / ".github/workflows/weekly-repo-research.yml").exists()
