
from __future__ import annotations

import argparse
import json
import os
import sys

from .orchestrator import KnowledgeOpsOrchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the review-gated knowledge-ops agents")
    parser.add_argument("--config", default=os.getenv("KNOWLEDGE_OPS_CONFIG", "config/project.json"))
    parser.add_argument("--policy", default=os.getenv("KNOWLEDGE_OPS_POLICY", "policies/agent-policy.json"))
    parser.add_argument("--output", default=os.getenv("KNOWLEDGE_OPS_OUTPUT", "generated"))
    parser.add_argument("--feedback", default=os.getenv("KNOWLEDGE_OPS_FEEDBACK", "feedback/decisions.jsonl"))
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = KnowledgeOpsOrchestrator(
        config_path=args.config,
        policy_path=args.policy,
        output_dir=args.output,
        feedback_path=args.feedback,
    ).run()
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
