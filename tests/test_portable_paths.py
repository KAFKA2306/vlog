from scripts.check_portable_paths import path_violations, validate_paths


def test_portable_paths_accept_spaces_and_unicode():
    assert path_violations("docs/日本語 path/README.md") == []


def test_portable_paths_reject_ads_and_reserved_names():
    assert path_violations("a/SKILL.md:Zone.Identifier")
    assert path_violations("docs/CON.txt")
    assert path_violations("docs/trailing.")


def test_portable_paths_reject_case_fold_collisions():
    failures = validate_paths(["Docs/README.md", "docs/readme.md"])
    assert set(failures) == {"Docs/README.md", "docs/readme.md"}
