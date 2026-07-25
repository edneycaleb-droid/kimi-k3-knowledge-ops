from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class KimiCapabilityProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = json.loads(
            (ROOT / "governance" / "kimi_capability_profile.json").read_text(encoding="utf-8")
        )

    def test_profile_is_pinned_and_fail_closed(self) -> None:
        self.assertEqual(len(self.data["canonical_forge"]["commit"]), 40)
        invariants = "\n".join(self.data["hard_invariants"])
        self.assertIn("OpenRouter is disabled", invariants)
        self.assertIn("No discovered upstream code is installed", invariants)
        self.assertIn("No capability promotes itself", invariants)

    def test_profile_covers_all_evaluation_lanes(self) -> None:
        lanes = {entry["id"] for entry in self.data["evaluation_lanes"]}
        self.assertEqual(
            lanes,
            {
                "protocol-parity",
                "tool-conformance",
                "long-context",
                "hardware-portability",
                "research-integrity",
            },
        )

    def test_validator_passes_repository_state(self) -> None:
        path = ROOT / "scripts" / "validate_kimi_capability_profile.py"
        spec = importlib.util.spec_from_file_location("validate_kimi_capability_profile", path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader
        spec.loader.exec_module(module)
        self.assertEqual(module.validate(), [])


if __name__ == "__main__":
    unittest.main()
