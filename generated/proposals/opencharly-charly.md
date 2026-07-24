# Integration proposal: opencharly/charly

## Decision

**REVIEW** — quality 71/100; bounded learning adjustment +0.

## Source

- Repository: https://github.com/opencharly/charly
- Categories: agent, mcp_server, memory, plugin, tool, workflow
- License: MIT
- Default branch: `main`
- Collected via: GitHub REST API GET only

## Ten-control assessment

- provenance: **10/10** — Canonical GitHub identity and retrieval timestamp
- source_authority: **7/10** — Trusted owner or non-fork upstream
- maintenance: **10/10** — Last push 0 days ago
- documentation: **10/10** — README length 48887
- license: **10/10** — SPDX MIT
- testing: **4/10** — Test/CI signal in sampled metadata
- security: **8/10** — 0 critical, 0 high findings
- interoperability: **5/10** — Compatibility target matches
- reproducibility: **5/10** — Versioned dependency manifest
- adoption: **2/10** — 0 stars

## Static security review

- `medium` `SEC008` in `README.md`: Elevated execution or privilege

## Generated implementation

A disabled metadata adapter was generated at `generated/adapters/opencharly-charly.json`.
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
