import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Dict, List


class GraphStorage:
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def add_triples(self, triples: List[Dict[str, Any]], source: str) -> None:
        with open(self.storage_path, "a", encoding="utf-8") as f:
            if not triples:
                f.write(
                    json.dumps(
                        {
                            "subject": "",
                            "predicate": "",
                            "object": "",
                            "_source": source,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
            else:
                for triple in triples:
                    triple["_source"] = source
                    f.write(json.dumps(triple, ensure_ascii=False) + "\n")

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.storage_path.exists():
            return []

        results = []
        query = query.lower()

        with open(self.storage_path, "r", encoding="utf-8") as f:
            for line in f:
                triple = json.loads(line)
                # Simple keyword search in subject, predicate, or object
                subject = triple.get("subject", "")
                predicate = triple.get("predicate", "")
                obj = triple.get("object", "")
                content = f"{subject} {predicate} {obj}".lower()
                if query in content:
                    results.append(triple)

        # Sort by relevance or just return latest (reversed)
        return list(reversed(results))[:limit]

    def get_context_string(self, triples: Sequence[Mapping[str, object]]) -> str:
        if not triples:
            return ""

        lines = []
        for t in triples:
            subject = t.get("subject")
            predicate = t.get("predicate")
            obj = t.get("object")
            source = t.get("_source")
            lines.append(f"- {subject} --[{predicate}]--> {obj} (Source: {source})")

        return "\n".join(lines)

    def is_source_processed(self, source: str) -> bool:
        if not self.storage_path.exists():
            return False

        with open(self.storage_path, "r", encoding="utf-8") as f:
            for line in f:
                triple = json.loads(line)
                if triple.get("_source") == source:
                    return True
        return False
