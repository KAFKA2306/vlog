from scripts.ingest_to_cognee import get_pending, refresh_queue


def test_refresh_queue_adds_new_summaries_and_preserves_status(tmp_path):
    summary_dir = tmp_path / "summaries"
    queue_path = tmp_path / "state" / "cognee_queue.yaml"
    summary_dir.mkdir()
    queue_path.parent.mkdir()

    (summary_dir / "20260101_summary.txt").write_text("old", encoding="utf-8")
    (summary_dir / "20260102_summary.txt").write_text("new", encoding="utf-8")
    queue_path.write_text(
        """
batch_size: 1
files:
  - name: 20260101_summary.txt
    status: completed
    error:
""".lstrip(),
        encoding="utf-8",
    )

    queue = refresh_queue(summary_dir, queue_path)

    assert queue["batch_size"] == 1
    assert queue["files"] == [
        {
            "name": "20260101_summary.txt",
            "status": "completed",
            "error": None,
        },
        {
            "name": "20260102_summary.txt",
            "status": "pending",
            "error": None,
        },
    ]
    assert get_pending(queue) == [queue["files"][1]]
