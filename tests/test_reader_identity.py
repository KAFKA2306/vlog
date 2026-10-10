from scripts.reader_identity import identity_failures

SHA = "a" * 40
GOOD = {
    "status": "ok",
    "environment": "production",
    "deploymentId": "dpl_x",
    "gitCommitSha": SHA,
    "gitCommitRef": "main",
}


def test_accepts_complete_identity() -> None:
    assert identity_failures(GOOD) == []
    assert identity_failures(GOOD, expected_sha=SHA) == []


def test_empty_or_missing_provenance_fails() -> None:
    for key in ("gitCommitSha", "gitCommitRef"):
        assert identity_failures({**GOOD, key: None})
        assert identity_failures({**GOOD, key: ""})
        assert identity_failures({k: v for k, v in GOOD.items() if k != key})


def test_mismatched_sha_or_ref_fails() -> None:
    assert identity_failures(GOOD, expected_sha="b" * 40)
    assert identity_failures({**GOOD, "gitCommitRef": "feature"})


def test_short_sha_and_bad_deployment_fail() -> None:
    assert identity_failures({**GOOD, "gitCommitSha": "abc1234"})
    assert identity_failures({**GOOD, "deploymentId": "x"})
    assert identity_failures({**GOOD, "environment": "preview"})
    assert identity_failures({**GOOD, "status": "degraded"})
