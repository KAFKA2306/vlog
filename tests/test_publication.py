from src.domain.publication import has_publishable_source


def test_short_source_is_not_publishable() -> None:
    assert not has_publishable_source(["You"], 50)


def test_source_over_minimum_is_publishable() -> None:
    assert has_publishable_source(["a" * 51], 50)


def test_multiple_sources_are_combined() -> None:
    assert has_publishable_source(["a" * 25, "b" * 26], 50)
