from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_profile_is_pinned_and_fail_closed() -> None:
    data = json.loads((ROOT / "governance" / "kimi_capability_profile.json").read_text(encoding="utf-8"))
    assert len(data["canonical_forge"]["commit"]) == 40
    invariants = "\n".join(data["hard_invariants"])
    assert "OpenRouter is disabled" in invariants
    assert "No discovered upstream code is installed" in invariants
    assert "No capability promotes itself" in invariants


def test_profile_covers_all_evaluation_lanes() -> None:
    data = json.loads((ROOT / "governance" / "kimi_capability_profile.json").read_text(encoding="utf-8"))
    lanes = {entry["id"] for entry in data["evaluation_lanes"]}
    assert lanes == {"protocol-parity", "tool-conformance", "long-context", "hardware-portability", "research-integrity"}


def test_validator_passes_repository_state() -> None:
    path = ROOT / "scripts" / "validate_kimi_capability_profile.py"
    spec = importlib.util.spec_from_file_location("validate_kimi_capability_profile", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    assert module.validate() == []
