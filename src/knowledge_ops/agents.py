
from __future__ import annotations

import hashlib
import json
import math
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .github_client import GitHubClient
from .models import (
    CandidateAssessment,
    QualityControl,
    RepositorySnapshot,
    SecurityFinding,
    utc_now,
)
from .policy import AgentPolicy


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:80]


class DiscoveryAgent:
    name = "discovery"

    def __init__(self, client: GitHubClient, config: dict[str, Any], policy: AgentPolicy):
        self.client = client
        self.config = config
        self.policy = policy

    def run(self) -> list[RepositorySnapshot]:
        snapshots: list[RepositorySnapshot] = []
        seen: set[str] = set()
        for full_name in self.config.get("seed_repositories", []):
            metadata = self.client.get_repository(full_name)
            snapshot = self.client.snapshot(metadata, "seed")
            snapshots.append(snapshot)
            seen.add(snapshot.canonical_id())
        remaining = self.policy.max_candidates_per_run - len(snapshots)
        if remaining <= 0:
            return snapshots
        queries = list(self.config.get("search_queries", []))
        per_query = max(1, min(10, math.ceil(remaining / max(len(queries), 1))))
        for query in queries:
            for metadata in self.client.search_repositories(query, per_page=per_query):
                if len(snapshots) >= self.policy.max_candidates_per_run:
                    return snapshots
                identity = str(metadata.get("full_name", "")).lower()
                if not identity or identity in seen:
                    continue
                snapshot = self.client.snapshot(metadata, query)
                snapshots.append(snapshot)
                seen.add(identity)
        return snapshots


class ClassificationAgent:
    name = "classification"

    RULES = {
        "mcp_server": (
            r"\bmodel context protocol\b",
            r"\bmcp server\b",
            r"\bmcp_server\b",
            r'"mcpServers"\s*:',
        ),
        "skill": (
            r"\bagent skills?\b",
            r"\bskills? catalog\b",
            r"\bSKILL\.md\b",
            r"\bskill manifest\b",
        ),
        "tool": (
            r"\btools?\b",
            r"\bfunction calling\b",
            r"\btool use\b",
            r"\btool registry\b",
        ),
        "plugin": (r"\bplugins?\b", r"\bextension\b"),
        "agent": (r"\bai agents?\b", r"\bagentic\b", r"\borchestrat(or|ion)\b"),
        "workflow": (r"\bworkflow\b", r"\bcron\b", r"\bscheduler\b"),
        "memory": (r"\bmemory\b", r"\blearning loop\b", r"\bknowledge graph\b"),
        "api": (r"\brest api\b", r"\bopenapi\b", r"\bwebhook\b"),
    }

    def run(self, repository: RepositorySnapshot) -> list[str]:
        text = "\n".join(
            [repository.name, repository.description, repository.readme, *repository.sampled_files.values()]
        )
        categories = [
            category
            for category, patterns in self.RULES.items()
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
        ]
        topics = {topic.lower() for topic in repository.topics}
        if "mcp-server" in topics or "model-context-protocol" in topics:
            categories.append("mcp_server")
        if not categories:
            categories.append("uncategorized")
        return sorted(set(categories))


class DeduplicationAgent:
    name = "deduplication"

    def run(self, repositories: Iterable[RepositorySnapshot]) -> list[RepositorySnapshot]:
        by_identity: dict[str, RepositorySnapshot] = {}
        for repository in repositories:
            key = repository.canonical_id()
            current = by_identity.get(key)
            if current is None or self._rank(repository) > self._rank(current):
                by_identity[key] = repository
        # Detect near-identical forks using normalized README digest and retain the stronger source.
        by_digest: dict[str, RepositorySnapshot] = {}
        for repository in by_identity.values():
            normalized = re.sub(r"\s+", " ", repository.readme.lower()).strip()
            digest = hashlib.sha256(normalized.encode()).hexdigest() if len(normalized) > 500 else repository.canonical_id()
            current = by_digest.get(digest)
            if current is None or self._rank(repository) > self._rank(current):
                by_digest[digest] = repository
        return sorted(by_digest.values(), key=lambda item: item.full_name.lower())

    @staticmethod
    def _rank(repository: RepositorySnapshot) -> tuple[int, int, int]:
        return (0 if repository.fork else 1, repository.stars, repository.forks)


class ProvenanceAgent:
    name = "provenance"

    def run(self, repository: RepositorySnapshot) -> dict[str, Any]:
        file_digests = {
            path: hashlib.sha256(content.encode("utf-8")).hexdigest()
            for path, content in sorted(repository.sampled_files.items())
        }
        receipt = {
            "canonical_repository": repository.full_name,
            "canonical_url": repository.html_url,
            "api_url": repository.api_url,
            "default_branch": repository.default_branch,
            "fetched_at": repository.fetched_at,
            "source_query": repository.source_query,
            "metadata_digest": hashlib.sha256(
                json.dumps(repository.to_dict(), sort_keys=True).encode()
            ).hexdigest(),
            "sampled_file_digests": file_digests,
            "collection_method": "GitHub REST API GET only",
            "executed_upstream_code": False,
            "installed_upstream_dependencies": False,
        }
        return receipt


class SecurityAgent:
    name = "security"

    RULES = [
        ("SEC001", "critical", r"(curl|wget)[^\n|]{0,200}\|\s*(sh|bash|zsh)", "Remote shell execution"),
        ("SEC002", "critical", r"\b(nc|ncat|netcat)\b.{0,80}\s-e\s", "Reverse-shell behavior"),
        ("SEC003", "critical", r"\b(xmrig|minerd|cryptominer|stratum\+tcp)\b", "Cryptocurrency miner indicator"),
        ("SEC004", "high", r"\b(os\.system|subprocess\.(run|Popen|call)|child_process\.(exec|spawn))\b", "Process execution capability"),
        ("SEC005", "high", r"\b(eval|exec)\s*\(", "Dynamic code execution"),
        ("SEC006", "high", r"(~\/\.ssh|id_rsa|AWS_SECRET_ACCESS_KEY|GITHUB_TOKEN|ANTHROPIC_API_KEY|OPENAI_API_KEY)", "Credential or secret access"),
        ("SEC007", "high", r'"(preinstall|install|postinstall)"\s*:', "Package installation lifecycle hook"),
        ("SEC008", "medium", r"\b(chmod\s+\+x|sudo\s+|--privileged|hostNetwork\s*:\s*true)\b", "Elevated execution or privilege"),
        ("SEC009", "medium", r"\b(base64\.(b64decode|decodebytes)|atob)\b.{0,160}\b(exec|eval|system|spawn)\b", "Encoded payload execution"),
        ("SEC010", "medium", r"\b(disable.*(antivirus|firewall)|security scan bypass)\b", "Security-control bypass"),
    ]

    def run(self, repository: RepositorySnapshot) -> list[SecurityFinding]:
        findings: list[SecurityFinding] = []
        for path, content in repository.sampled_files.items():
            for rule_id, severity, pattern, description in self.RULES:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    evidence = re.sub(r"\s+", " ", match.group(0))[:180]
                    findings.append(
                        SecurityFinding(
                            rule_id=rule_id,
                            severity=severity,
                            path=path,
                            evidence=evidence,
                            description=description,
                        )
                    )
        return findings


class ExtractionAgent:
    name = "extraction"

    ENV_PATTERN = re.compile(r"\b([A-Z][A-Z0-9_]{2,})\b")
    URL_PATTERN = re.compile(r"https://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+")

    def run(self, repository: RepositorySnapshot, categories: list[str]) -> dict[str, Any]:
        text = "\n".join(repository.sampled_files.values())
        env_names = sorted(
            {
                name
                for name in self.ENV_PATTERN.findall(text)
                if any(token in name for token in ("KEY", "TOKEN", "URL", "HOST", "PORT", "SECRET"))
            }
        )[:40]
        endpoints = sorted(set(self.URL_PATTERN.findall(text)))[:40]
        package_json = self._json_file(repository, "package.json")
        mcp_manifests = {
            path: self._safe_json(content)
            for path, content in repository.sampled_files.items()
            if path.endswith(("mcp.json", ".mcp.json", "server.json"))
        }
        commands: dict[str, str] = {}
        if isinstance(package_json, dict):
            for key, value in (package_json.get("scripts") or {}).items():
                if key in {"start", "serve", "build", "test"} and isinstance(value, str):
                    commands[key] = value[:300]
        return {
            "categories": categories,
            "language": repository.language,
            "topics": repository.topics,
            "environment_variable_names": env_names,
            "documented_https_endpoints": endpoints,
            "mcp_manifests": mcp_manifests,
            "package_scripts_for_review": commands,
            "has_dockerfile": "Dockerfile" in repository.sampled_files,
            "has_python_manifest": "pyproject.toml" in repository.sampled_files,
            "has_node_manifest": "package.json" in repository.sampled_files,
        }

    @staticmethod
    def _safe_json(content: str) -> Any:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"parse_error": True}

    def _json_file(self, repository: RepositorySnapshot, path: str) -> Any:
        content = repository.sampled_files.get(path)
        return self._safe_json(content) if content else None


class CompatibilityAgent:
    name = "compatibility"

    def __init__(self, config: dict[str, Any]):
        self.targets = [str(item).lower() for item in config.get("compatibility_targets", [])]

    def run(
        self, repository: RepositorySnapshot, categories: list[str], extracted: dict[str, Any]
    ) -> dict[str, Any]:
        haystack = " ".join(
            [
                repository.name,
                repository.description,
                " ".join(repository.topics),
                " ".join(categories),
                repository.readme[:10000],
            ]
        ).lower()
        matched = [target for target in self.targets if target in haystack]
        transports = []
        for transport in ("stdio", "sse", "streamable-http", "websocket"):
            if transport in haystack:
                transports.append(transport)
        runtimes = []
        if extracted.get("has_python_manifest") or repository.language == "Python":
            runtimes.append("python")
        if extracted.get("has_node_manifest") or repository.language in {"TypeScript", "JavaScript"}:
            runtimes.append("node")
        return {
            "targets_matched": sorted(set(matched)),
            "mcp_transports": sorted(set(transports)),
            "candidate_runtimes": sorted(set(runtimes)),
            "integration_mode": "metadata_adapter_only",
        }


class LearningAgent:
    name = "learning"

    def __init__(self, feedback_path: str | Path):
        self.feedback_path = Path(feedback_path)

    def _events(self) -> list[dict[str, Any]]:
        if not self.feedback_path.exists():
            return []
        events = []
        for line in self.feedback_path.read_text(encoding="utf-8").splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if item.get("decision") in {"accepted", "rejected"}:
                events.append(item)
        return events

    def run(self, repository: RepositorySnapshot, categories: list[str]) -> tuple[int, dict[str, Any]]:
        owner_stats: dict[str, list[int]] = defaultdict(list)
        category_stats: dict[str, list[int]] = defaultdict(list)
        for event in self._events():
            value = 1 if event["decision"] == "accepted" else -1
            if event.get("owner"):
                owner_stats[str(event["owner"]).lower()].append(value)
            for category in event.get("categories", []):
                category_stats[str(category)].append(value)
        evidence: dict[str, Any] = {"bounded": True, "events_considered": 0}
        raw = 0.0
        owner_values = owner_stats.get(repository.owner.lower(), [])
        if owner_values:
            raw += sum(owner_values) / len(owner_values) * 5
            evidence["events_considered"] += len(owner_values)
        for category in categories:
            values = category_stats.get(category, [])
            if values:
                raw += sum(values) / len(values)
                evidence["events_considered"] += len(values)
        adjustment = max(-10, min(10, round(raw)))
        evidence["adjustment"] = adjustment
        evidence["changes_code"] = False
        evidence["changes_security_policy"] = False
        return adjustment, evidence


class QualityAgent:
    name = "quality"

    def __init__(self, config: dict[str, Any], policy: AgentPolicy):
        self.trusted_owners = {str(item).lower() for item in config.get("trusted_owners", [])}
        self.policy = policy

    def run(
        self,
        repository: RepositorySnapshot,
        categories: list[str],
        security_findings: list[SecurityFinding],
        compatibility: dict[str, Any],
    ) -> tuple[list[QualityControl], int]:
        now = datetime.now(timezone.utc)
        pushed = _parse_date(repository.pushed_at)
        age_days = (now - pushed).days if pushed else 9999
        critical = sum(item.severity == "critical" for item in security_findings)
        high = sum(item.severity == "high" for item in security_findings)
        has_tests = any(
            token in "\n".join(repository.sampled_files).lower()
            for token in ("test", "ci.yml", "pytest", "jest")
        )
        controls = [
            QualityControl("provenance", 10 if repository.html_url and repository.fetched_at else 0, "Canonical GitHub identity and retrieval timestamp"),
            QualityControl("source_authority", 10 if repository.owner.lower() in self.trusted_owners else (7 if not repository.fork else 3), "Trusted owner or non-fork upstream"),
            QualityControl("maintenance", 10 if age_days <= 30 else 8 if age_days <= 90 else 5 if age_days <= 365 else 2, f"Last push {age_days} days ago"),
            QualityControl("documentation", 10 if len(repository.readme) >= 4000 else 8 if len(repository.readme) >= 1500 else 5 if len(repository.readme) >= 400 else 1, f"README length {len(repository.readme)}"),
            QualityControl("license", 10 if repository.license_spdx in self.policy.allowed_licenses else (4 if repository.license_spdx else 0), f"SPDX {repository.license_spdx or 'missing'}"),
            QualityControl("testing", 10 if has_tests else 4, "Test/CI signal in sampled metadata"),
            QualityControl("security", 0 if critical else 3 if high else 8 if security_findings else 10, f"{critical} critical, {high} high findings"),
            QualityControl("interoperability", min(10, 3 + 2 * len(compatibility.get("targets_matched", []))), "Compatibility target matches"),
            QualityControl("reproducibility", 10 if repository.sampled_files.get("pyproject.toml") or repository.sampled_files.get("package.json") else 5, "Versioned dependency manifest"),
            QualityControl("adoption", 10 if repository.stars >= 1000 else 8 if repository.stars >= 250 else 6 if repository.stars >= 50 else 4 if repository.stars >= 10 else 2, f"{repository.stars} stars"),
        ]
        score = round(sum(control.score for control in controls))
        return controls, score


class DecisionAgent:
    name = "decision"

    def __init__(self, config: dict[str, Any]):
        self.min_quality = int(config.get("min_quality_score", 60))
        self.candidate_quality = int(config.get("candidate_quality_score", 80))

    def run(self, assessment: CandidateAssessment) -> tuple[str, list[str]]:
        reasons: list[str] = []
        severities = {finding.severity for finding in assessment.security_findings}
        adjusted = max(0, min(100, assessment.quality_score + assessment.learning_adjustment))
        if "critical" in severities:
            return "blocked", ["Critical static-security finding"]
        if assessment.repository.archived or assessment.repository.disabled:
            return "rejected", ["Repository is archived or disabled"]
        if assessment.repository.license_spdx is None:
            reasons.append("License requires manual verification")
        if "high" in severities:
            reasons.append("High-severity capability requires manual security review")
        if adjusted < self.min_quality:
            return "rejected", reasons + [f"Adjusted quality {adjusted} below {self.min_quality}"]
        if adjusted >= self.candidate_quality and "high" not in severities:
            return "candidate", reasons + [f"Adjusted quality {adjusted} meets candidate threshold"]
        return "review", reasons + [f"Adjusted quality {adjusted} requires human review"]


class ProposalAgent:
    name = "proposal"

    def __init__(self, output_dir: str | Path, project_id: str):
        self.output_dir = Path(output_dir)
        self.project_id = project_id

    def run(self, assessment: CandidateAssessment) -> tuple[str | None, str | None]:
        if assessment.decision not in {"candidate", "review"}:
            return None, None
        slug = _slug(assessment.repository.full_name)
        proposals = self.output_dir / "proposals"
        adapters = self.output_dir / "adapters"
        receipts = self.output_dir / "receipts"
        proposals.mkdir(parents=True, exist_ok=True)
        adapters.mkdir(parents=True, exist_ok=True)
        receipts.mkdir(parents=True, exist_ok=True)

        adapter = {
            "schema_version": 1,
            "status": "disabled_pending_review",
            "project": self.project_id,
            "source_repository": assessment.repository.full_name,
            "source_url": assessment.repository.html_url,
            "categories": assessment.categories,
            "compatibility": assessment.compatibility,
            "environment_variable_names": assessment.extracted.get("environment_variable_names", []),
            "documented_https_endpoints": assessment.extracted.get("documented_https_endpoints", []),
            "mcp_manifests": assessment.extracted.get("mcp_manifests", {}),
            "execution": {
                "enabled": False,
                "auto_install": False,
                "auto_execute": False,
                "activation_requires_human_approval": True,
            },
            "provenance_receipt": f"generated/receipts/{slug}.json",
        }
        adapter_path = adapters / f"{slug}.json"
        adapter_path.write_text(json.dumps(adapter, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        receipt_path = receipts / f"{slug}.json"
        receipt_path.write_text(
            json.dumps(assessment.provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        findings = "\n".join(
            f"- `{finding.severity}` `{finding.rule_id}` in `{finding.path}`: {finding.description}"
            for finding in assessment.security_findings
        ) or "- No sampled static-security indicators."
        controls = "\n".join(
            f"- {control.name}: **{control.score}/10** — {control.evidence}"
            for control in assessment.quality_controls
        )
        proposal = f"""# Integration proposal: {assessment.repository.full_name}

## Decision

**{assessment.decision.upper()}** — quality {assessment.quality_score}/100; bounded learning adjustment {assessment.learning_adjustment:+d}.

## Source

- Repository: {assessment.repository.html_url}
- Categories: {", ".join(assessment.categories)}
- License: {assessment.repository.license_spdx or "unverified"}
- Default branch: `{assessment.repository.default_branch}`
- Collected via: GitHub REST API GET only

## Ten-control assessment

{controls}

## Static security review

{findings}

## Generated implementation

A disabled metadata adapter was generated at `generated/adapters/{slug}.json`.
It contains normalized MCP/tool/skill metadata and compatibility hints. It cannot install or execute upstream code.

## Activation checklist

- [ ] Confirm maintainer and license provenance.
- [ ] Review every static-security finding.
- [ ] Pin an immutable upstream revision.
- [ ] Run upstream code only in an isolated, disposable sandbox.
- [ ] Add repository-owned adapter tests.
- [ ] Approve least-privilege credentials and network access.
- [ ] Enable the adapter in a separate reviewed pull request.

## Safety invariants

- Upstream code executed during discovery: **no**
- Upstream dependencies installed during discovery: **no**
- Automatic merge: **no**
- Human approval required before activation: **yes**
"""
        proposal_path = proposals / f"{slug}.md"
        proposal_path.write_text(proposal, encoding="utf-8")
        return str(proposal_path), str(adapter_path)
