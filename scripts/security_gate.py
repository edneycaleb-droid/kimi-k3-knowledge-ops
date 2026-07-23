
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "policies/agent-policy.json"
CORE = ROOT / "src/knowledge_ops"

FORBIDDEN_IMPORTS = {
    "subprocess",
    "pty",
    "pexpect",
}
FORBIDDEN_CALLS = {
    "eval",
    "exec",
    "compile",
    "__import__",
    "os.system",
    "os.popen",
    "subprocess.run",
    "subprocess.Popen",
    "subprocess.call",
}
REQUIRED_FALSE = {
    "execute_discovered_code",
    "install_discovered_dependencies",
    "run_discovered_containers",
    "follow_untrusted_instructions",
    "auto_merge_proposals",
}


def dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        left = dotted_name(node.value)
        return f"{left}.{node.attr}" if left else node.attr
    return ""


def main() -> int:
    failures: list[str] = []
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    for key in sorted(REQUIRED_FALSE):
        if policy.get(key) is not False:
            failures.append(f"policy must set {key}=false")
    if policy.get("network_mode") != "github_read_only":
        failures.append("network_mode must be github_read_only")
    if set(policy.get("allowed_hosts", [])) != {"api.github.com"}:
        failures.append("allowed_hosts must be exactly api.github.com")

    for path in CORE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [alias.name.split(".")[0] for alias in node.names]
                for name in names:
                    if name in FORBIDDEN_IMPORTS:
                        failures.append(f"{path}: forbidden import {name}")
            if isinstance(node, ast.Call):
                name = dotted_name(node.func)
                if name in FORBIDDEN_CALLS:
                    failures.append(f"{path}: forbidden call {name}")
        text = path.read_text(encoding="utf-8").lower()
        if "pip install" in text or "npm install" in text or "docker run" in text:
            failures.append(f"{path}: core runtime may not install or run discovered code")

    workflow = (ROOT / ".github/workflows/autonomous-research.yml").read_text(encoding="utf-8")
    if "pull-requests: write" not in workflow:
        failures.append("autonomous workflow must create reviewable pull requests")
    if "main" in workflow and "git push origin main" in workflow:
        failures.append("autonomous workflow may not push directly to main")
    if "gh pr merge" in workflow or "auto-merge" in workflow:
        failures.append("autonomous workflow may not merge proposals")

    if failures:
        print("SECURITY GATE FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("SECURITY GATE PASSED: fail-closed discovery and review-only implementation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
