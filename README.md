# Kimi K3 Knowledge Ops

Autonomous, review-gated discovery and integration intelligence for Kimi K3, Kimi Code, MCP servers, skills, tools, and agent workflows.

This repository runs an autonomous **eleven-agent** knowledge-operations loop that
discovers GitHub projects, classifies skills/tools/MCP servers, deduplicates forks,
records provenance, performs static security screening, extracts integration metadata,
checks compatibility, learns from bounded reviewer feedback, scores ten quality
controls, makes a decision, and generates disabled implementation adapters plus
reviewable pull requests.

## Safety boundary

The discovery loop never installs dependencies from discovered repositories, never
executes discovered code or containers, never follows instructions embedded in
untrusted content, and never merges its own proposals. Critical static findings are
blocked. Every generated adapter is `disabled_pending_review`.

## Agents

1. Discovery
2. Deduplication
3. Classification
4. Provenance
5. Security
6. Extraction
7. Compatibility
8. Bounded learning
9. Ten-control quality scoring
10. Decision
11. Proposal and disabled adapter generation

## Continuous operation

`.github/workflows/autonomous-research.yml` runs at minutes 7 and 37 of every hour.
It scans GitHub with read-only API calls, runs all tests and gates, and opens or refreshes
a pull request containing `generated/` proposals. It does not push to `main`.

Run locally:

```bash
python -m pip install -e .
python -m knowledge_ops
python scripts/run_all_checks.py
python -m knowledge_ops.service
```

Service endpoints:

- `GET /health`
- `GET /ready`
- `GET /metrics`
- `GET /catalog`
- `POST /run` with `Authorization: Bearer $KNOWLEDGE_OPS_RUN_TOKEN`

## dlt verified-source ingestion

GitHub has an official dlt verified source. The optional pipeline loads seed-repository
events incrementally into DuckDB:

```bash
python -m pip install -r requirements-dlt.txt
dlt --non-interactive --yes --disable-telemetry init github duckdb
python pipelines/github_verified_pipeline.py
```

Real credentials belong in `.dlt/secrets.toml` or environment variables; that file is
gitignored. The scheduled dlt workflow stores the DuckDB file as a short-lived Actions
artifact rather than committing database state.

## CreateOS

`createos.json`, `Dockerfile`, and `CREATEOS.md` define a production VCS deployment on
Python 3.12, port 3000, with health/readiness probes and security scanning enabled.
CreateOS auto-deploys on push after the repository is connected.

## Quality target

`scripts/quality_gate.py` requires all ten platform controls to pass. The score is a
verifiable repository gate, not a claim that unknown third-party software is perfect.
