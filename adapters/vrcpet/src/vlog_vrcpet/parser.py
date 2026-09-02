from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ParseIssue:
    code: str
    message: str
    line_number: int | None = None
    raw_fragment: str | None = None


@dataclass(frozen=True, slots=True)
class ParsedObservation:
    observation_type: str
    records: tuple[dict[str, Any], ...]
    issues: tuple[ParseIssue, ...] = ()


def _decode(raw_bytes: bytes) -> tuple[str, list[ParseIssue]]:
    text = raw_bytes.decode("utf-8", errors="replace")
    issues: list[ParseIssue] = []
    if "\ufffd" in text:
        issues.append(
            ParseIssue(
                code="invalid_utf8",
                message="invalid UTF-8 bytes were replaced while parsing",
            )
        )
    return text, issues


def _parse_jsonl(text: str, issues: list[ParseIssue]) -> tuple[dict[str, Any], ...]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            issues.append(
                ParseIssue(
                    code="malformed_jsonl_line",
                    message=str(exc),
                    line_number=line_number,
                    raw_fragment=line,
                )
            )
            continue
        if isinstance(value, dict):
            records.append(value)
        else:
            issues.append(
                ParseIssue(
                    code="non_object_jsonl_record",
                    message="JSONL record was preserved under the value key",
                    line_number=line_number,
                    raw_fragment=line,
                )
            )
            records.append({"value": value})
    return tuple(records)


def _parse_document(text: str, issues: list[ParseIssue]) -> tuple[dict[str, Any], ...]:
    if not text.strip():
        return ()
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        issues.append(
            ParseIssue(
                code="malformed_json_document",
                message=str(exc),
                raw_fragment=text,
            )
        )
        return ()
    if isinstance(value, dict):
        return (value,)
    issues.append(
        ParseIssue(
            code="non_object_json_document",
            message="JSON document was preserved under the value key",
        )
    )
    return ({"value": value},)


def _parse_pet_log(text: str, issues: list[ParseIssue]) -> tuple[dict[str, Any], ...]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        stripped = line.strip()
        if stripped.startswith(("{", "[")):
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                issues.append(
                    ParseIssue(
                        code="malformed_pet_log_json",
                        message=str(exc),
                        line_number=line_number,
                        raw_fragment=line,
                    )
                )
                records.append({"raw_text": line})
                continue
            if isinstance(value, dict):
                records.append(value)
            else:
                records.append({"value": value})
        else:
            records.append({"raw_text": line})
    return tuple(records)


def parse_observation(relative_path: str, raw_bytes: bytes) -> ParsedObservation:
    name = Path(relative_path).name.lower()
    text, issues = _decode(raw_bytes)

    if name == "profile.json":
        return ParsedObservation(
            observation_type="profile",
            records=_parse_document(text, issues),
            issues=tuple(issues),
        )
    if name == "heard_nouns.json":
        return ParsedObservation(
            observation_type="vocabulary",
            records=_parse_document(text, issues),
            issues=tuple(issues),
        )
    if name == "pet.log":
        return ParsedObservation(
            observation_type="operational",
            records=_parse_pet_log(text, issues),
            issues=tuple(issues),
        )
    if name.endswith(".jsonl"):
        return ParsedObservation(
            observation_type="conversation",
            records=_parse_jsonl(text, issues),
            issues=tuple(issues),
        )
    raise ValueError(f"unsupported VRCPet source file: {relative_path}")
