import pytest

from src.infrastructure.strict_sync import StrictSupabaseSync


class Response:
    def __init__(self, data):
        self.data = data


class Query:
    def __init__(self, data):
        self.data = data

    def upsert(self, rows, on_conflict):
        return self

    def execute(self):
        return Response(self.data)


class Client:
    def __init__(self, data):
        self.data = data

    def table(self, name):
        return Query(self.data)


def test_unconfigured_sync_fails(monkeypatch) -> None:
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    with pytest.raises(RuntimeError, match="not configured"):
        StrictSupabaseSync()


def test_zero_record_sync_fails(monkeypatch) -> None:
    sync = StrictSupabaseSync(client=Client([]))
    monkeypatch.setattr(sync, "_sync_summaries", lambda: 0)
    monkeypatch.setattr(sync, "_sync_novels", lambda: 0)
    monkeypatch.setattr(sync, "_sync_photos", lambda: 0)
    monkeypatch.setattr(sync, "_sync_evaluations", lambda: 0)
    with pytest.raises(RuntimeError, match="zero verified records"):
        sync.sync()


def test_upsert_requires_matching_rows() -> None:
    sync = StrictSupabaseSync(client=Client([{"id": 1}]))
    with pytest.raises(RuntimeError, match="expected 2 rows, got 1"):
        sync._verified_upsert("daily_entries", [{"a": 1}, {"a": 2}], "a")
