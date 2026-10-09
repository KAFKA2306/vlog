from __future__ import annotations

import random
import struct

from vlog_companion import (
    TermMemory,
    choose,
    encode_reading,
    observe,
    synced_parameter_bits,
    weight,
)
from vlog_vrchat_osc import osc_message


def test_observe_increments_frequency() -> None:
    state: dict[str, TermMemory] = {}
    observe(state, "猫", "ネコ", 100.0)
    memory = observe(state, "猫", "ネコ", 200.0)
    assert memory.count == 2
    assert memory.last_seen == 200.0


def test_weight_prefers_frequency_and_recency() -> None:
    now = 10 * 86400.0
    frequent = TermMemory("猫", "ネコ", 5, now)
    rare = TermMemory("犬", "イヌ", 1, now)
    old = TermMemory("鳥", "トリ", 5, 0.0)
    assert weight(frequent, now) > weight(rare, now)
    assert weight(frequent, now) > weight(old, now)


def test_choose_returns_observed_memory() -> None:
    memory = TermMemory("猫", "ネコ", 1, 0.0)
    assert choose([memory], 0.0, random.Random(1)) == memory


def test_kana_encoding_and_parameter_budget() -> None:
    assert encode_reading("ねこ")[:2] == encode_reading("ネコ")[:2]
    assert len(encode_reading("ネコ")) == 8
    assert synced_parameter_bits() == 73


def test_osc_packets_match_vrchat_parameter_shape() -> None:
    int_packet = osc_message("/avatar/parameters/PetChar0", 7)
    bool_packet = osc_message("/avatar/parameters/PetSpeak", True)
    assert int_packet.endswith(struct.pack(">i", 7))
    assert b",i\0" in int_packet
    assert b",T\0" in bool_packet
