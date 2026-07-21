# Security policy

Treat every fetched artifact as untrusted input.

## Private reporting

Do not disclose vulnerabilities in public issues or pull requests. Use GitHub's private reporting form:
https://github.com/edneycaleb-droid/kimi-k3-knowledge-ops/security/advisories/new

Include affected paths, impact, reproduction details, and suggested containment. Do not include real credentials.

## Ingestion boundaries

- Never execute, source, import, install, or activate discovered code.
- Never expose repository, organization, runner, or user secrets to research jobs.
- Fetch only allowlisted first-party endpoints.
- Store canonical URL, retrieval timestamp, upstream revision, license when applicable, and SHA-256 digest.
- Flag binaries, obfuscation, install hooks, network side effects, credential access, persistence, and prompt-injection content.
- Require owner review before expanding the allowlist or changing permissions.
