
# CreateOS deployment

This repository is ready for a CreateOS VCS project.

## Project settings

Use the values in `createos.json`:

- Runtime: `python:3.12`
- Port: `3000`
- Install: `python -m pip install --no-cache-dir -e .`
- Build: `python -m compileall -q src && python scripts/quality_gate.py && python scripts/security_gate.py`
- Run: `python -m knowledge_ops.service`
- Health: `/health`
- Readiness: `/ready`
- Security scan: enabled

Set runtime environment variables in CreateOS, never in Git:

- `GITHUB_TOKEN`: read-only GitHub token used for live discovery.
- `KNOWLEDGE_OPS_RUN_TOKEN`: bearer token required for `POST /run`.
- `PORT`: CreateOS injects this; default is 3000.

The service exposes read-only `/health`, `/ready`, `/metrics`, and `/catalog` endpoints.
A run can only be started with `Authorization: Bearer <KNOWLEDGE_OPS_RUN_TOKEN>`.

CreateOS MCP tools are not available in every ChatGPT connection. When available, create
a VCS project from this repository and use the checked-in settings. Auto-deploy on push
then keeps the service current.
