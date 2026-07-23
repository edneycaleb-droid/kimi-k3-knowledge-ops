
from __future__ import annotations

import json
import os
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

from .agents import (
    ClassificationAgent,
    CompatibilityAgent,
    DecisionAgent,
    DeduplicationAgent,
    DiscoveryAgent,
    ExtractionAgent,
    LearningAgent,
    ProposalAgent,
    ProvenanceAgent,
    QualityAgent,
    SecurityAgent,
)
from .github_client import GitHubClient
from .models import CandidateAssessment, RunReport, utc_now
from .policy import AgentPolicy


class KnowledgeOpsOrchestrator:
    """Runs a deterministic, review-gated multi-agent research loop."""

    AGENT_NAMES = (
        "discovery",
        "deduplication",
        "classification",
        "provenance",
        "security",
        "extraction",
        "compatibility",
        "learning",
        "quality",
        "decision",
        "proposal",
    )

    def __init__(
        self,
        config_path: str | Path,
        policy_path: str | Path,
        output_dir: str | Path = "generated",
        feedback_path: str | Path = "feedback/decisions.jsonl",
        client: GitHubClient | None = None,
    ):
        self.config = json.loads(Path(config_path).read_text(encoding="utf-8"))
        self.policy = AgentPolicy.load(policy_path)
        self.output_dir = Path(output_dir)
        self.feedback_path = Path(feedback_path)
        self.client = client or GitHubClient(self.policy)

    def run(self) -> RunReport:
        started = utc_now()
        run_id = f"{started[:10]}-{uuid.uuid4().hex[:10]}"
        metrics: dict[str, Any] = {"agents": {}, "safety": {}}

        discovery = DiscoveryAgent(self.client, self.config, self.policy)
        raw = discovery.run()
        metrics["agents"]["discovery"] = {"outputs": len(raw)}

        unique = DeduplicationAgent().run(raw)
        metrics["agents"]["deduplication"] = {
            "inputs": len(raw),
            "outputs": len(unique),
            "removed": len(raw) - len(unique),
        }

        classifier = ClassificationAgent()
        provenance = ProvenanceAgent()
        security = SecurityAgent()
        extraction = ExtractionAgent()
        compatibility = CompatibilityAgent(self.config)
        learning = LearningAgent(self.feedback_path)
        quality = QualityAgent(self.config, self.policy)
        decision = DecisionAgent(self.config)
        proposal = ProposalAgent(self.output_dir, self.config["project_id"])

        assessments: list[CandidateAssessment] = []
        for repository in unique:
            assessment = CandidateAssessment(repository=repository)
            assessment.categories = classifier.run(repository)
            assessment.provenance = provenance.run(repository)
            assessment.security_findings = security.run(repository)
            assessment.extracted = extraction.run(repository, assessment.categories)
            assessment.compatibility = compatibility.run(
                repository, assessment.categories, assessment.extracted
            )
            adjustment, learning_evidence = learning.run(repository, assessment.categories)
            assessment.learning_adjustment = adjustment
            assessment.extracted["learning_evidence"] = learning_evidence
            assessment.quality_controls, assessment.quality_score = quality.run(
                repository,
                assessment.categories,
                assessment.security_findings,
                assessment.compatibility,
            )
            assessment.decision, assessment.decision_reasons = decision.run(assessment)
            assessment.proposal_path, assessment.adapter_path = proposal.run(assessment)
            assessments.append(assessment)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        catalog = {
            "schema_version": 1,
            "project_id": self.config["project_id"],
            "generated_at": utc_now(),
            "entries": [item.to_dict() for item in assessments],
        }
        (self.output_dir / "catalog.json").write_text(
            json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        decisions = Counter(item.decision for item in assessments)
        metrics["agents"].update(
            {
                name: {"status": "completed"}
                for name in self.AGENT_NAMES
                if name not in metrics["agents"]
            }
        )
        metrics["decisions"] = dict(decisions)
        metrics["safety"] = {
            "executed_discovered_code": False,
            "installed_discovered_dependencies": False,
            "auto_merged": False,
            "policy_digest": self.policy.digest,
        }
        report = RunReport(
            run_id=run_id,
            project_id=self.config["project_id"],
            started_at=started,
            finished_at=utc_now(),
            candidates_discovered=len(raw),
            candidates_unique=len(unique),
            proposals_created=sum(item.proposal_path is not None for item in assessments),
            blocked=decisions.get("blocked", 0),
            assessments=assessments,
            agent_metrics=metrics,
            policy_digest=self.policy.digest,
        )
        (self.output_dir / "latest-run.json").write_text(
            json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (self.output_dir / "metrics.json").write_text(
            json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return report
