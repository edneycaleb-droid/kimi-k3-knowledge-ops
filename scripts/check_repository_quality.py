#!/usr/bin/env python3
"""Deterministic, network-free ten-control repository quality validator."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTROLS = {
    "readme_status": ["README.md", "STATUS.md"],
    "contributing": ["CONTRIBUTING.md"],
    "security_private_reporting": ["SECURITY.md"],
    "codeowners": [".github/CODEOWNERS"],
    "issue_forms": [".github/ISSUE_TEMPLATE/bug.yml", ".github/ISSUE_TEMPLATE/research.yml", ".github/ISSUE_TEMPLATE/config.yml"],
    "pull_request_template": [".github/pull_request_template.md"],
    "dependency_policy": [".github/dependabot.yml"],
    "deterministic_fallback": ["scripts/check_repository_quality.py"],
    "safe_workflow": [".github/workflows/research-update.yml"],
    "clean_tracking": [".github/ISSUE_TEMPLATE/config.yml"],
}

failures = []
for control, paths in CONTROLS.items():
    missing = [path for path in paths if not (ROOT / path).is_file()]
    if missing:
        failures.append(f"{control}: missing {', '.join(missing)}")

def text(path):
    return (ROOT / path).read_text(encoding="utf-8")

if not failures:
    security = text("SECURITY.md").lower()
    workflow = text(".github/workflows/research-update.yml")
    sources = text("sources/official.yml")
    owners = text(".github/CODEOWNERS")
    intake = text(".github/ISSUE_TEMPLATE/config.yml")
    checks = [
        ("security_private_reporting", "security/advisories/new" in security and "public issue" in security),
        ("valid_codeowners", "@edneycaleb-droid" in owners),
        ("private_issue_routing", "blank_issues_enabled: false" in intake and "security/advisories/new" in intake),
        ("read_only_permissions", re.search(r"permissions:\s*\n\s*contents:\s*read", workflow) is not None),
        ("immutable_checkout", re.search(r"actions/checkout@[0-9a-f]{40}", workflow) is not None),
        ("credentials_disabled", "persist-credentials: false" in workflow),
        ("bounded_runtime", "timeout-minutes: 5" in workflow),
        ("offline_validator_executed", "python scripts/check_repository_quality.py" in workflow),
        ("source_execution_blocked", "execute_discovered_code: false" in sources),
        ("source_install_blocked", "install_discovered_code: false" in sources),
    ]
    failures.extend(name for name, passed in checks if not passed)

if failures:
    print("REPOSITORY_QUALITY_SCORE=FAIL")
    for failure in failures:
        print(f"- {failure}")
    sys.exit(1)

print("REPOSITORY_QUALITY_SCORE=10/10")
print("controls=" + ",".join(CONTROLS))
