
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class PolicyError(RuntimeError):
    """Raised when a safety invariant is violated."""


@dataclass(frozen=True, slots=True)
class AgentPolicy:
    raw: dict[str, Any]

    @classmethod
    def load(cls, path: str | Path) -> "AgentPolicy":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        policy = cls(data)
        policy.validate()
        return policy

    def validate(self) -> None:
        required_false = (
            "execute_discovered_code",
            "install_discovered_dependencies",
            "run_discovered_containers",
            "follow_untrusted_instructions",
            "auto_merge_proposals",
        )
        for key in required_false:
            if self.raw.get(key) is not False:
                raise PolicyError(f"Fail-closed policy requires {key}=false")
        if self.raw.get("network_mode") != "github_read_only":
            raise PolicyError("network_mode must be github_read_only")
        if self.raw.get("proposal_mode") != "pull_request":
            raise PolicyError("proposal_mode must be pull_request")
        if int(self.raw.get("max_file_bytes", 0)) <= 0:
            raise PolicyError("max_file_bytes must be positive")
        if int(self.raw.get("max_candidates_per_run", 0)) <= 0:
            raise PolicyError("max_candidates_per_run must be positive")

    @property
    def max_file_bytes(self) -> int:
        return int(self.raw["max_file_bytes"])

    @property
    def max_candidates_per_run(self) -> int:
        return int(self.raw["max_candidates_per_run"])

    @property
    def allowed_hosts(self) -> set[str]:
        return set(self.raw["allowed_hosts"])

    @property
    def allowed_licenses(self) -> set[str]:
        return set(self.raw["allowed_licenses"])

    @property
    def digest(self) -> str:
        canonical = json.dumps(self.raw, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(canonical).hexdigest()
