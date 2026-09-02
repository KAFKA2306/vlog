from __future__ import annotations

import json
from pathlib import Path

import pytest
from vlog_vrcpet.runner import run_ingest


def _roots(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    project = tmp_path / "checkout"
    source = tmp_path / "vrcpet-data"
    private = tmp_path / "private-evidence"
    state = tmp_path / "state"
    (source / "logs").mkdir(parents=True)
    return project, source, private, state


def test_missing_source_is_a_durable_skip(tmp_path: Path) -> None:
    _, _, private, state = _roots(tmp_path)

    summary = run_ingest(
        source_root=tmp_path / "does-not-exist",
        project_root=tmp_path / "checkout",
        private_root=private,
        state_root=state,
        run_id="skip-run",
    )

    assert summary.status == "skipped"
    assert json.loads(summary.output_path.read_text()) == {
        "discovered": 0,
        "failed": 0,
        "ingested": 0,
        "parse_issues": 0,
        "run_id": "skip-run",
        "skipped": 0,
        "status": "skipped",
    }
    assert not private.exists()


def test_ingest_persists_private_bytes_and_is_idempotent(tmp_path: Path) -> None:
    project, source, private, state = _roots(tmp_path)
    conversation = b'{"t":"heard","text":"private phrase"}\n'
    (source / "logs" / "2026-09-02.jsonl").write_bytes(conversation)
    (source / "profile.json").write_text('{"name":"pet"}', encoding="utf-8")

    first = run_ingest(
        source_root=source,
        project_root=project,
        private_root=private,
        state_root=state,
        run_id="first-run",
    )
    second = run_ingest(
        source_root=source,
        project_root=project,
        private_root=private,
        state_root=state,
        run_id="second-run",
    )

    assert first.status == "succeeded"
    assert first.ingested == 2
    assert second.status == "succeeded"
    assert second.ingested == 0
    assert second.skipped == 2
    assert (private / "vrcpet/conversation").is_dir()
    assert (private / "vrcpet/profile").is_dir()
    assert len(state.joinpath("vrcpet/ledger.jsonl").read_text().splitlines()) == 2
    assert conversation == (source / "logs" / "2026-09-02.jsonl").read_bytes()


def test_public_state_does_not_contain_observation_text(tmp_path: Path) -> None:
    project, source, private, state = _roots(tmp_path)
    secret_text = "private phrase must stay in evidence"
    (source / "logs" / "2026-09-02.jsonl").write_text(
        f'{{"text":"{secret_text}"}}\n{{broken\n', encoding="utf-8"
    )

    summary = run_ingest(
        source_root=source,
        project_root=project,
        private_root=private,
        state_root=state,
        run_id="privacy-run",
    )

    assert summary.parse_issues == 1
    public_state = "\n".join(
        path.read_text(encoding="utf-8")
        for path in state.joinpath("vrcpet").rglob("*")
        if path.is_file()
    )
    assert secret_text not in public_state
    assert "raw_fragment" not in public_state


def test_private_evidence_cannot_be_inside_checkout(tmp_path: Path) -> None:
    project, source, _, state = _roots(tmp_path)
    (source / "logs" / "2026-09-02.jsonl").write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="outside the repository"):
        run_ingest(
            source_root=source,
            project_root=project,
            private_root=project / "data" / "private-evidence",
            state_root=state,
        )
