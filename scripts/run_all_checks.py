
from __future__ import annotations

import subprocess
import sys


COMMANDS = [
    [sys.executable, "-m", "compileall", "-q", "src", "pipelines", "scripts", "tests"],
    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
    [sys.executable, "scripts/quality_gate.py"],
    [sys.executable, "scripts/security_gate.py"],
]


def main() -> int:
    for command in COMMANDS:
        print("+", " ".join(command), flush=True)
        result = subprocess.run(command, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
