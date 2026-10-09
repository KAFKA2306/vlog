from dataclasses import dataclass
from enum import Enum
from typing import Any


class AuditState(Enum):
    PASS = "pass"
    FAIL = "fail"
    UNVERIFIED = "unverified"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class AuditFinding:
    check_name: str
    state: AuditState
    evidence: str
    details: str | None = None
    source: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class AuditReport:
    findings: tuple[AuditFinding, ...]

    @property
    def has_blockers(self) -> bool:
        return any(
            finding.state in {AuditState.FAIL, AuditState.UNVERIFIED}
            for finding in self.findings
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "findings": [
                {
                    "check_name": finding.check_name,
                    "state": finding.state.value,
                    "evidence": finding.evidence,
                    "details": finding.details,
                    "source": finding.source,
                    "metadata": finding.metadata or {},
                }
                for finding in self.findings
            ]
        }
