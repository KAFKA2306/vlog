from __future__ import annotations

from vlog_vrchat_osc import VrchatOsc


class RecordingOsc(VrchatOsc):
    def __init__(self) -> None:
        self.ints: list[tuple[str, int]] = []
        self.bools: list[tuple[str, bool]] = []

    def send_int(self, name: str, value: int) -> None:
        self.ints.append((name, value))

    def send_bool(self, name: str, value: bool) -> None:
        self.bools.append((name, value))


def test_speak_emits_only_petchar_zero_through_seven() -> None:
    osc = RecordingOsc()
    osc.speak([-1, 1, 300, 3, 4, 5, 6, 7, 8, 9], mood=999, pulse_seconds=0)

    assert osc.ints[:8] == [
        ("PetChar0", 0),
        ("PetChar1", 1),
        ("PetChar2", 255),
        ("PetChar3", 3),
        ("PetChar4", 4),
        ("PetChar5", 5),
        ("PetChar6", 6),
        ("PetChar7", 7),
    ]
    assert osc.ints[8:] == [("PetMood", 255)]
    assert osc.bools == [("PetSpeak", True), ("PetSpeak", False)]
