# Contributing

This repository curates official Moonshot AI and Kimi K3 research; it is not an upstream product fork.

1. Open or update an issue describing the source or catalog change.
2. Prefer first-party sources listed in `sources/official.yml`.
3. Record canonical URL, retrieval date, upstream revision, license when applicable, and SHA-256 digest.
4. Do not add executable binaries, secrets, copied credentials, install hooks, or automatically activated code.
5. Keep discovered skills, tools, and MCP servers as inert metadata until separately reviewed.
6. Run `python scripts/check_repository_quality.py`.
7. Submit a focused pull request using the repository template.

Preserve upstream names, licenses, and attribution. Security reports must follow `SECURITY.md`, not public issues.
