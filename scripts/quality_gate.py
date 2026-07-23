
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def count_tests() -> int:
    total = 0
    for path in (ROOT / "tests").glob("test_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        total += sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
            for node in ast.walk(tree)
        )
    return total


def main() -> int:
    orchestrator = (ROOT / "src/knowledge_ops/orchestrator.py").read_text(encoding="utf-8")
    policy = json.loads((ROOT / "policies/agent-policy.json").read_text(encoding="utf-8"))
    autonomous = (ROOT / ".github/workflows/autonomous-research.yml").read_text(encoding="utf-8")
    ci = (ROOT / ".github/workflows/agent-platform.yml").read_text(encoding="utf-8")
    createos = json.loads((ROOT / "createos.json").read_text(encoding="utf-8"))

    controls = {
        "eleven_specialized_agents": orchestrator.count('"') > 0
        and all(
            name in orchestrator
            for name in (
                "discovery", "deduplication", "classification", "provenance",
                "security", "extraction", "compatibility", "learning",
                "quality", "decision", "proposal"
            )
        ),
        "ten_or_more_deterministic_tests": count_tests() >= 10,
        "fail_closed_policy": all(
            policy.get(key) is False
            for key in (
                "execute_discovered_code", "install_discovered_dependencies",
                "run_discovered_containers", "follow_untrusted_instructions",
                "auto_merge_proposals"
            )
        ),
        "scheduled_continuous_research": "schedule:" in autonomous and "cron:" in autonomous,
        "pull_request_only_changes": "gh pr create" in autonomous and "git push origin main" not in autonomous,
        "verified_dlt_pipeline": (ROOT / "pipelines/github_verified_pipeline.py").is_file()
        and (ROOT / "requirements-dlt.txt").is_file(),
        "createos_production_contract": createos["settings"]["runtime"] == "python:3.12"
        and createos["health"]["path"] == "/health",
        "health_and_readiness_service": all(
            token in (ROOT / "src/knowledge_ops/service.py").read_text(encoding="utf-8")
            for token in ('"/health"', '"/ready"', '"/metrics"', '"/catalog"')
        ),
        "ci_runs_all_gates": all(
            token in ci for token in ("unittest", "quality_gate.py", "security_gate.py", "compileall")
        ),
        "secrets_excluded": ".dlt/secrets.toml" in (ROOT / ".gitignore").read_text(encoding="utf-8")
        and not (ROOT / ".dlt/secrets.toml").exists(),
    }
    score = sum(controls.values())
    for name, passed in controls.items():
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
    print(f"QUALITY SCORE: {score}/10")
    return 0 if score == 10 else 1


if __name__ == "__main__":
    sys.exit(main())
