# AI Ecosystem Curator

This repository uses the canonical AI Ecosystem Curator skill maintained at:

- `edneycaleb-droid/hermes-ai-knowledge-ops/.chatgpt/skills/ai-ecosystem-curator/SKILL.md`
- `edneycaleb-droid/hermes-ai-knowledge-ops/00_AI_ECOSYSTEM_INDEX.md`

## Required behavior

When evaluating AI tools, repositories, models, MCP servers, research feeds, or infrastructure:

1. Verify identity and current facts using official sources.
2. Classify each candidate as **ADOPT, PILOT, WATCH, REFERENCE, QUARANTINE, or REJECT**.
3. Separate architecture worth copying from software worth installing.
4. Prefer local-first, open-source, auditable, provider-agnostic components.
5. Require security, maintenance, cost, license, sandbox, and architectural-fit gates.
6. Never expose credentials, production sessions, sensitive data, or real repositories to unverified tools.
7. Preserve findings in `00_AI_ECOSYSTEM_INDEX.md` and the canonical Hermes registry.
8. Use isolated branches/worktrees for code changes and require tests before merge.

The canonical skill is the authoritative version. Update it first and keep this pointer stable.
