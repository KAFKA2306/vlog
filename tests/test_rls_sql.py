import re
from pathlib import Path


def test_rls_has_no_public_write_all_policy() -> None:
    sql = Path("infra/supabase/schema.sql").read_text(encoding="utf-8").lower()
    assert not re.search(r"for\s+all\s+using\s*\(\s*true\s*\)", sql)
    assert "to anon, authenticated" in sql
    assert "using (is_public = true)" in sql
    assert "from public, anon, authenticated" in sql
    assert "grant select on table public.daily_entries" in sql
    assert "grant select on table public.novels" in sql
