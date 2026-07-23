
from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from .models import RepositorySnapshot
from .policy import AgentPolicy, PolicyError


@dataclass(slots=True)
class GitHubClient:
    policy: AgentPolicy
    token: str | None = None
    timeout_seconds: int = 20
    user_agent: str = "knowledge-ops-agent/1.0"

    def __post_init__(self) -> None:
        if self.token is None:
            self.token = os.getenv("GITHUB_TOKEN")

    def _request_json(self, url: str) -> Any:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in self.policy.allowed_hosts:
            raise PolicyError(f"Blocked network target: {url}")
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": self.user_agent,
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = response.read(self.policy.max_file_bytes * 4)
                return json.loads(payload)
        except urllib.error.HTTPError as exc:
            if exc.code == 403 and exc.headers.get("X-RateLimit-Remaining") == "0":
                reset = exc.headers.get("X-RateLimit-Reset", "unknown")
                raise RuntimeError(f"GitHub API rate limit exhausted; resets at {reset}") from exc
            raise RuntimeError(f"GitHub API returned {exc.code} for {url}") from exc

    def search_repositories(self, query: str, per_page: int = 10) -> list[dict[str, Any]]:
        limit = min(max(per_page, 1), 25)
        encoded = urllib.parse.urlencode(
            {"q": query, "sort": "updated", "order": "desc", "per_page": limit}
        )
        data = self._request_json(f"https://api.github.com/search/repositories?{encoded}")
        return list(data.get("items", []))

    def get_repository(self, full_name: str) -> dict[str, Any]:
        safe = "/".join(urllib.parse.quote(part, safe="") for part in full_name.split("/", 1))
        return self._request_json(f"https://api.github.com/repos/{safe}")

    def get_content(self, full_name: str, path: str, ref: str | None = None) -> str:
        repo = "/".join(urllib.parse.quote(part, safe="") for part in full_name.split("/", 1))
        safe_path = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
        url = f"https://api.github.com/repos/{repo}/contents/{safe_path}"
        if ref:
            url += "?" + urllib.parse.urlencode({"ref": ref})
        try:
            data = self._request_json(url)
        except RuntimeError:
            return ""
        if not isinstance(data, dict) or data.get("type") != "file":
            return ""
        if int(data.get("size", 0)) > self.policy.max_file_bytes:
            return ""
        if data.get("encoding") == "base64":
            raw = base64.b64decode(data.get("content", ""), validate=False)
            return raw[: self.policy.max_file_bytes].decode("utf-8", errors="replace")
        return str(data.get("content", ""))[: self.policy.max_file_bytes]

    def snapshot(self, metadata: dict[str, Any], source_query: str) -> RepositorySnapshot:
        full_name = str(metadata["full_name"])
        default_branch = str(metadata.get("default_branch") or "main")
        sample_paths = [
            "README.md",
            "README",
            "pyproject.toml",
            "requirements.txt",
            "package.json",
            "server.json",
            "mcp.json",
            ".mcp.json",
            "Dockerfile",
            "docker-compose.yml",
            ".github/workflows/ci.yml",
            ".github/workflows/test.yml",
            "LICENSE",
            "LICENSE.md",
        ]
        files: dict[str, str] = {}
        for path in sample_paths:
            content = self.get_content(full_name, path, default_branch)
            if content:
                files[path] = content
            if sum(len(v.encode("utf-8")) for v in files.values()) >= self.policy.max_file_bytes * 3:
                break
            time.sleep(0.01)
        readme = files.get("README.md") or files.get("README") or ""
        license_obj = metadata.get("license") or {}
        return RepositorySnapshot(
            full_name=full_name,
            html_url=str(metadata.get("html_url") or ""),
            api_url=str(metadata.get("url") or ""),
            owner=str((metadata.get("owner") or {}).get("login") or full_name.split("/")[0]),
            name=str(metadata.get("name") or full_name.split("/")[-1]),
            description=str(metadata.get("description") or ""),
            default_branch=default_branch,
            stars=int(metadata.get("stargazers_count") or 0),
            forks=int(metadata.get("forks_count") or 0),
            open_issues=int(metadata.get("open_issues_count") or 0),
            archived=bool(metadata.get("archived")),
            disabled=bool(metadata.get("disabled")),
            fork=bool(metadata.get("fork")),
            license_spdx=license_obj.get("spdx_id"),
            pushed_at=metadata.get("pushed_at"),
            created_at=metadata.get("created_at"),
            updated_at=metadata.get("updated_at"),
            topics=list(metadata.get("topics") or []),
            language=metadata.get("language"),
            readme=readme,
            sampled_files=files,
            source_query=source_query,
        )
