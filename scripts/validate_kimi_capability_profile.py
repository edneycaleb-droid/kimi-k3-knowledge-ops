from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "governance" / "kimi_capability_profile.json"
SKILLS = {
    "kimi-protocol-parity-lab",
    "kimi-tool-conformance-auditor",
    "long-context-retention-lab",
    "inference-portability-benchmark",
}


def validate() -> list[str]:
    errors: list[str] = []
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    forge = data.get("canonical_forge", {})
    if len(str(forge.get("commit", ""))) != 40:
        errors.append("canonical forge must pin a 40-character commit")
    invariants = "\n".join(data.get("hard_invariants", []))
    for phrase in ("OpenRouter is disabled", "No capability promotes itself", "finite time"):
        if phrase not in invariants:
            errors.append(f"missing invariant: {phrase}")
    lanes = {item.get("id") for item in data.get("evaluation_lanes", [])}
    required_lanes = {"protocol-parity", "tool-conformance", "long-context", "hardware-portability", "research-integrity"}
    if not required_lanes.issubset(lanes):
        errors.append(f"missing evaluation lanes: {sorted(required_lanes - lanes)}")
    for name in SKILLS:
        path = ROOT / ".agents" / "skills" / name / "SKILL.md"
        if not path.is_file():
            errors.append(f"missing skill: {name}")
            continue
        text = path.read_text(encoding="utf-8")
        for required in (f"name: {name}", "## Contract", "## Workflow", "## Limits", "## Output", "Non-goals"):
            if required not in text:
                errors.append(f"{name} missing {required}")
        if "max_" not in text:
            errors.append(f"{name} lacks a finite limit")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"- {error}")
        return 1
    print("Kimi capability profile validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
