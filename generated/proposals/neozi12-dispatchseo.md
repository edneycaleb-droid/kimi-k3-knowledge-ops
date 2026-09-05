# Integration proposal: NeoZi12/dispatchseo

## Decision

**REVIEW** — quality 69/100; bounded learning adjustment +0.

## Source

- Repository: https://github.com/NeoZi12/dispatchseo
- Categories: agent, mcp_server, memory, skill, tool, workflow
- License: AGPL-3.0
- Default branch: `main`
- Collected via: GitHub REST API GET only

## Ten-control assessment

- provenance: **10/10** — Canonical GitHub identity and retrieval timestamp
- source_authority: **7/10** — Trusted owner or non-fork upstream
- maintenance: **10/10** — Last push 0 days ago
- documentation: **10/10** — README length 15455
- license: **4/10** — SPDX AGPL-3.0
- testing: **4/10** — Test/CI signal in sampled metadata
- security: **3/10** — 0 critical, 1 high findings
- interoperability: **5/10** — Compatibility target matches
- reproducibility: **10/10** — Versioned dependency manifest
- adoption: **6/10** — 55 stars

## Static security review

- `high` `SEC006` in `docker-compose.yml`: Credential or secret access

## Generated implementation

A disabled metadata adapter was generated at `generated/adapters/neozi12-dispatchseo.json`.
It contains normalized MCP/tool/skill metadata and compatibility hints. It cannot install or execute upstream code.

## Activation checklist

- [ ] Confirm maintainer and license provenance.
- [ ] Review every static-security finding.
- [ ] Pin an immutable upstream revision.
- [ ] Run upstream code only in an isolated, disposable sandbox.
- [ ] Add repository-owned adapter tests.
- [ ] Approve least-privilege credentials and network access.
- [ ] Enable the adapter in a separate reviewed pull request.

## Safety invariants

- Upstream code executed during discovery: **no**
- Upstream dependencies installed during discovery: **no**
- Automatic merge: **no**
- Human approval required before activation: **yes**
