
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(slots=True)
class RepositorySnapshot:
    full_name: str
    html_url: str
    api_url: str
    owner: str
    name: str
    description: str = ""
    default_branch: str = "main"
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    archived: bool = False
    disabled: bool = False
    fork: bool = False
    license_spdx: str | None = None
    pushed_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    topics: list[str] = field(default_factory=list)
    language: str | None = None
    readme: str = ""
    sampled_files: dict[str, str] = field(default_factory=dict)
    source_query: str = ""
    fetched_at: str = field(default_factory=utc_now)

    def canonical_id(self) -> str:
        return self.full_name.lower().strip()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SecurityFinding:
    rule_id: str
    severity: str
    path: str
    evidence: str
    description: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class QualityControl:
    name: str
    score: int
    evidence: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CandidateAssessment:
    repository: RepositorySnapshot
    categories: list[str] = field(default_factory=list)
    extracted: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    security_findings: list[SecurityFinding] = field(default_factory=list)
    quality_controls: list[QualityControl] = field(default_factory=list)
    quality_score: int = 0
    compatibility: dict[str, Any] = field(default_factory=dict)
    learning_adjustment: int = 0
    decision: str = "review"
    decision_reasons: list[str] = field(default_factory=list)
    proposal_path: str | None = None
    adapter_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["repository"] = self.repository.to_dict()
        data["security_findings"] = [item.to_dict() for item in self.security_findings]
        data["quality_controls"] = [item.to_dict() for item in self.quality_controls]
        return data


@dataclass(slots=True)
class RunReport:
    run_id: str
    project_id: str
    started_at: str
    finished_at: str
    candidates_discovered: int
    candidates_unique: int
    proposals_created: int
    blocked: int
    assessments: list[CandidateAssessment]
    agent_metrics: dict[str, Any]
    policy_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "project_id": self.project_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "candidates_discovered": self.candidates_discovered,
            "candidates_unique": self.candidates_unique,
            "proposals_created": self.proposals_created,
            "blocked": self.blocked,
            "assessments": [item.to_dict() for item in self.assessments],
            "agent_metrics": self.agent_metrics,
            "policy_digest": self.policy_digest,
        }
