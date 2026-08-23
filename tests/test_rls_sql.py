SECURITY_MIGRATION = "infra/supabase/migrations/20260802070700_secure_rls.sql"


def test_rls_has_no_public_write_all_policy() -> None:
    with open(SECURITY_MIGRATION, encoding="utf-8") as handle:
        sql = handle.read().lower()
    assert "forallusing(true)" not in "".join(sql.split())
    assert "to anon, authenticated" in sql
    assert "using (is_public = true)" in sql
    assert "from public, anon, authenticated" in sql
    assert "grant select on table public.daily_entries" in sql
    assert "grant select on table public.novels" in sql
