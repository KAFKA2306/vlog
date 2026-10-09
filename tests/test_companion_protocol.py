from __future__ import annotations

from vlog_companion import SLOTS, normalize_chars


def test_normalize_chars_is_exactly_eight_bytes() -> None:
    assert SLOTS == 8
    assert normalize_chars([-1, 1, 300]) == [0, 1, 255, 0, 0, 0, 0, 0]
    assert normalize_chars(list(range(12))) == list(range(8))
