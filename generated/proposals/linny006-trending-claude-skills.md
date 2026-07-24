# Integration proposal: linny006/trending-claude-skills

## Decision

**REVIEW** — quality 69/100; bounded learning adjustment +0.

## Source

- Repository: https://github.com/linny006/trending-claude-skills
- Categories: agent, mcp_server, memory, plugin, skill, tool, workflow
- License: unverified
- Default branch: `master`
- Collected via: GitHub REST API GET only

## Ten-control assessment

- provenance: **10/10** — Canonical GitHub identity and retrieval timestamp
- source_authority: **7/10** — Trusted owner or non-fork upstream
- maintenance: **10/10** — Last push 0 days ago
- documentation: **10/10** — README length 15692
- license: **0/10** — SPDX missing
- testing: **4/10** — Test/CI signal in sampled metadata
- security: **10/10** — 0 critical, 0 high findings
- interoperability: **9/10** — Compatibility target matches
- reproducibility: **5/10** — Versioned dependency manifest
- adoption: **4/10** — 18 stars

## Static security review

- No sampled static-security indicators.

## Generated implementation

A disabled metadata adapter was generated at `generated/adapters/linny006-trending-claude-skills.json`.
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
