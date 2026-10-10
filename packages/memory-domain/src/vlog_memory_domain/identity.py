from __future__ import annotations

from hashlib import sha256
from pathlib import PurePosixPath
from typing import Any, Mapping

from .models import (
    PrivacyLevel,
    SourceObject,
    _is_machine_local_locator,
    _validate_object_uri,
    _validate_sha256,
)

_REQUIRED_KEYS = (
    "id",
    "kind",
    "object_uri",
    "sha256",
    "size_bytes",
    "recorded_at",
    "privacy",
)


def _leaks_local_path(value: str) -> bool:
    return (
        _is_machine_local_locator(value)
        or ".." in PurePosixPath(value.replace("\\", "/")).parts
    )


def _walk_strings(value: Any, where: str) -> None:
    if isinstance(value, str):
        if _leaks_local_path(value):
            raise ValueError(f"{where} must not contain a machine-local path")
    elif isinstance(value, Mapping):
        for key, item in value.items():
            _walk_strings(item, f"{where}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _walk_strings(item, f"{where}[{index}]")


def validate_source_manifest(manifest: Mapping[str, Any]) -> None:
    for key in _REQUIRED_KEYS:
        if key not in manifest:
            raise ValueError(f"manifest requires {key}")
    _validate_sha256(manifest["sha256"], "sha256")
    _validate_object_uri(manifest["object_uri"], PrivacyLevel(manifest["privacy"]))
    filename = manifest.get("original_filename")
    if filename is not None and (
        "/" in filename or "\\" in filename or _is_machine_local_locator(filename)
    ):
        raise ValueError("original_filename must be a bare file name")
    _walk_strings(manifest.get("metadata", {}), "metadata")


def verify_source_hash(source: SourceObject, data: bytes) -> None:
    if len(data) != source.size_bytes:
        raise ValueError("size_bytes mismatch between source object and content")
    if sha256(data).hexdigest() != source.sha256.lower():
        raise ValueError("sha256 mismatch between source object and content")
