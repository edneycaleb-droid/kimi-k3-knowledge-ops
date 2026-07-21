# Security and ingestion policy

Treat every fetched artifact as untrusted.

- Never execute, source, import, install, or activate discovered code.
- Never pass secrets to research or ingestion steps.
- Restrict retrieval to allowlisted first-party sources.
- Preserve canonical URL, retrieval timestamp, upstream revision, and SHA-256 digest.
- Screen for binaries, obfuscation, install hooks, network side effects, credential access, persistence, and prompt-injection content.
- Require human review before accepting new sources or enabling write permissions.
