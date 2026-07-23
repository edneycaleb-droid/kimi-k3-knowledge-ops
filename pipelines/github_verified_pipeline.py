"""Incrementally load official GitHub repository events with dlt's verified source.

Bootstrap once in a clean working tree:
    python -m pip install -r requirements-dlt.txt
    dlt init github duckdb

The generated ``github`` package is dlt's verified source. This adapter deliberately
imports it only when the pipeline is executed so the core agent platform remains
dependency-free and never installs code during discovery.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


def load_project_config(path: str | Path = "config/project.json") -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def split_repository(full_name: str) -> tuple[str, str]:
    owner, separator, name = full_name.partition("/")
    if not separator or not owner or not name:
        raise ValueError(f"Invalid GitHub repository identity: {full_name!r}")
    return owner, name


def _emit_github_error(exc: BaseException, secret: str | None = None) -> None:
    message = f"{type(exc).__name__}: {exc}"
    if secret:
        message = message.replace(secret, "***")
    message = (
        message.replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
    )
    print(
        f"::error file=pipelines/github_verified_pipeline.py,line=1,"
        f"title=dlt verified GitHub load::{message}",
        flush=True,
    )


def main() -> None:
    repository_root = str(Path(__file__).resolve().parents[1])
    if repository_root not in sys.path:
        sys.path.insert(0, repository_root)
    try:
        import dlt
        from github import github_repo_events
    except ImportError as exc:
        raise SystemExit(
            "Verified GitHub source is not initialized. Run: "
            "python -m pip install -r requirements-dlt.txt && dlt init github duckdb"
        ) from exc

    config = load_project_config(os.getenv("KNOWLEDGE_OPS_CONFIG", "config/project.json"))
    destination_name = os.getenv("DLT_DESTINATION", "duckdb")
    dataset_name = os.getenv("DLT_DATASET_NAME", config["dataset_name"])
    access_token = os.getenv("GITHUB_TOKEN") or os.getenv("SOURCES__GITHUB__ACCESS_TOKEN")
    if destination_name == "duckdb":
        destination: Any = dlt.destinations.duckdb(
            credentials=os.getenv("DLT_DUCKDB_PATH", "knowledge_ops.duckdb")
        )
    else:
        destination = destination_name
    pipeline = dlt.pipeline(
        pipeline_name=f"{config['project_id'].replace('-', '_')}_github_events",
        destination=destination,
        dataset_name=dataset_name,
    )
    for full_name in config["seed_repositories"]:
        owner, name = split_repository(full_name)
        source = github_repo_events(owner, name, access_token=access_token)
        load_info = pipeline.run(source)
        print(load_info)


if __name__ == "__main__":
    try:
        main()
    except BaseException as error:
        _emit_github_error(
            error,
            os.getenv("GITHUB_TOKEN") or os.getenv("SOURCES__GITHUB__ACCESS_TOKEN"),
        )
        raise
