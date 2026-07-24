# Integration proposal: open-metadata/OpenMetadata

## Decision

**REVIEW** — quality 79/100; bounded learning adjustment +0.

## Source

- Repository: https://github.com/open-metadata/OpenMetadata
- Categories: agent, mcp_server, memory, tool, workflow
- License: Apache-2.0
- Default branch: `main`
- Collected via: GitHub REST API GET only

## Ten-control assessment

- provenance: **10/10** — Canonical GitHub identity and retrieval timestamp
- source_authority: **7/10** — Trusted owner or non-fork upstream
- maintenance: **10/10** — Last push 0 days ago
- documentation: **10/10** — README length 19444
- license: **10/10** — SPDX Apache-2.0
- testing: **4/10** — Test/CI signal in sampled metadata
- security: **3/10** — 0 critical, 1 high findings
- interoperability: **5/10** — Compatibility target matches
- reproducibility: **10/10** — Versioned dependency manifest
- adoption: **10/10** — 14552 stars

## Static security review

- `high` `SEC007` in `package.json`: Package installation lifecycle hook

## Generated implementation

A disabled metadata adapter was generated at `generated/adapters/open-metadata-openmetadata.json`.
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
