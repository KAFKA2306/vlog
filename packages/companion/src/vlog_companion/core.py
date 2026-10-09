from __future__ import annotations

import math
import random
from dataclasses import dataclass

KANA = "アイウエオカキクケコガギグゲゴサシスセソザジズゼゾタチツテトダヂヅデドナニヌネノハヒフヘホバビブベボパピプペポマミムメモヤユヨラリルレロワヲンァィゥェォャュョッーヴ"
KANA_TO_INT = {char: index + 1 for index, char in enumerate(KANA)}
SLOTS = 8
WEIGHT_ALPHA = 0.5
WEIGHT_BETA = 0.8
DECAY_PER_DAY = 0.035


@dataclass(frozen=True)
class TermMemory:
    text: str
    reading: str
    count: int
    last_seen: float


def observe(
    state: dict[str, TermMemory],
    text: str,
    reading: str,
    now: float,
) -> TermMemory:
    current = state.get(text)
    memory = TermMemory(
        text=text,
        reading=reading,
        count=(current.count if current else 0) + 1,
        last_seen=now,
    )
    state[text] = memory
    return memory


def weight(
    memory: TermMemory,
    now: float,
    alpha: float = WEIGHT_ALPHA,
    beta: float = WEIGHT_BETA,
    decay_per_day: float = DECAY_PER_DAY,
) -> float:
    age_days = max(0.0, now - memory.last_seen) / 86400.0
    return (memory.count + alpha) ** beta * math.exp(-decay_per_day * age_days)


def choose(
    memories: list[TermMemory],
    now: float,
    rng: random.Random | None = None,
) -> TermMemory | None:
    if not memories:
        return None
    random_source = rng or random.Random()
    weights = [weight(memory, now) for memory in memories]
    return random_source.choices(memories, weights=weights, k=1)[0]


def katakana(text: str) -> str:
    chars = []
    for char in text:
        code = ord(char)
        chars.append(chr(code + 0x60) if 0x3041 <= code <= 0x3096 else char)
    return "".join(chars)


def encode_reading(reading: str, slots: int = SLOTS) -> list[int]:
    values = [KANA_TO_INT.get(char, 0) for char in katakana(reading)[:slots]]
    return values + [0] * (slots - len(values))


def normalize_chars(chars: list[int], slots: int = SLOTS) -> list[int]:
    values = [max(0, min(255, int(value))) for value in chars[:slots]]
    return values + [0] * (slots - len(values))


def synced_parameter_bits(slots: int = SLOTS) -> int:
    return slots * 8 + 8 + 1
