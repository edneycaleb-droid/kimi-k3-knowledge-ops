from __future__ import annotations
import base64
import json
import shutil
import zlib
from pathlib import Path

def main() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = "".join(
        path.read_text(encoding="ascii")
        for path in sorted((root / ".bootstrap").glob("payload.part*"))
    )
    files = json.loads(zlib.decompress(base64.b64decode(payload)).decode("utf-8"))
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    shutil.rmtree(root / ".bootstrap")
    (root / ".github/workflows/bootstrap-platform.yml").unlink(missing_ok=True)
    print(f"materialized {len(files)} tested platform files")

if __name__ == "__main__":
    main()
