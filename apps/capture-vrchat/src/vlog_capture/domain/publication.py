from collections.abc import Iterable


def has_publishable_source(texts: Iterable[str], minimum_bytes: int) -> bool:
    source_texts = tuple(texts)
    return (
        bool(source_texts)
        and sum(len(text.encode("utf-8")) for text in source_texts) > minimum_bytes
    )
