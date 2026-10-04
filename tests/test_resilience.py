from __future__ import annotations

import email.message
import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from knowledge_ops.agents import DiscoveryAgent  # noqa: E402
from knowledge_ops.github_client import GitHubClient, GitHubTransientError  # noqa: E402
from knowledge_ops.policy import AgentPolicy  # noqa: E402


def http_error(code: int, headers: dict[str, str] | None = None) -> urllib.error.HTTPError:
    msg = email.message.Message()
    for key, value in (headers or {}).items():
        msg[key] = value
    return urllib.error.HTTPError("https://api.github.com/x", code, "err", msg, io.BytesIO(b"{}"))


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class ClientRetryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = AgentPolicy.load(ROOT / "policies/agent-policy.json")
        self.client = GitHubClient(self.policy, token="t", request_spacing_seconds=0)

    def test_secondary_rate_limit_is_retried(self) -> None:
        responses = [http_error(403), http_error(502), FakeResponse(json.dumps({"ok": 1}).encode())]

        def fake_urlopen(*_a, **_k):
            item = responses.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen), mock.patch("time.sleep") as sleep:
            self.assertEqual(self.client._request_json("https://api.github.com/repos/a/b"), {"ok": 1})
        self.assertEqual(len([c for c in sleep.call_args_list if c.args and c.args[0] > 0]), 2)

    def test_not_found_is_not_retried(self) -> None:
        with mock.patch("urllib.request.urlopen", side_effect=http_error(404)) as opener, mock.patch("time.sleep"):
            with self.assertRaises(RuntimeError):
                self.client._request_json("https://api.github.com/repos/a/b")
        self.assertEqual(opener.call_count, 1)

    def test_retries_are_bounded(self) -> None:
        with mock.patch("urllib.request.urlopen", side_effect=http_error(503)) as opener, mock.patch("time.sleep"):
            with self.assertRaises(RuntimeError):
                self.client._request_json("https://api.github.com/repos/a/b")
        self.assertEqual(opener.call_count, self.client.max_attempts)

    def test_far_rate_limit_reset_is_clamped_not_fatal(self) -> None:
        exc = http_error(403, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "9999999999"})
        self.assertEqual(self.client._retry_delay(exc, 1), self.client.max_backoff_seconds)
        expired = http_error(403, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1"})
        self.assertEqual(self.client._retry_delay(expired, 1), 0.0)

    def test_every_attempt_is_spaced_even_on_errors(self) -> None:
        client = GitHubClient(self.policy, token="t", request_spacing_seconds=0.25)
        with mock.patch("urllib.request.urlopen", side_effect=http_error(404)), mock.patch("time.sleep") as sleep:
            self.assertEqual(client.get_content("a/b", "README.md"), "")
        self.assertIn(mock.call(0.25), sleep.call_args_list)

    def test_get_content_treats_404_as_absent(self) -> None:
        with mock.patch("urllib.request.urlopen", side_effect=http_error(404)), mock.patch("time.sleep"):
            self.assertEqual(self.client.get_content("a/b", "README.md"), "")

    def test_get_content_propagates_exhausted_transient_errors(self) -> None:
        with mock.patch("urllib.request.urlopen", side_effect=http_error(503)), mock.patch("time.sleep"):
            with self.assertRaises(GitHubTransientError):
                self.client.get_content("a/b", "README.md")

    def test_snapshot_fails_when_api_is_unavailable(self) -> None:
        metadata = {"full_name": "a/b", "default_branch": "main"}
        with mock.patch("urllib.request.urlopen", side_effect=http_error(503)), mock.patch("time.sleep"):
            with self.assertRaises(GitHubTransientError):
                self.client.snapshot(metadata, "q")


class DiscoveryToleranceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = AgentPolicy.load(ROOT / "policies/agent-policy.json")

    def test_one_failing_source_does_not_abort_run(self) -> None:
        client = mock.Mock()
        client.get_repository.side_effect = RuntimeError("GitHub API returned 403")
        client.search_repositories.return_value = [{"full_name": "acme/tool"}]
        snap = mock.Mock()
        snap.canonical_id.return_value = "acme/tool"
        client.snapshot.return_value = snap
        agent = DiscoveryAgent(client, {"seed_repositories": ["x/y"], "search_queries": ["q"]}, self.policy)
        with mock.patch("sys.stderr"):
            result = agent.run()
        self.assertEqual(result, [snap])
        self.assertEqual(len(agent.errors), 1)

    def test_total_failure_still_fails_loudly(self) -> None:
        client = mock.Mock()
        client.get_repository.side_effect = RuntimeError("down")
        client.search_repositories.side_effect = RuntimeError("down")
        agent = DiscoveryAgent(client, {"seed_repositories": ["x/y"], "search_queries": ["q"]}, self.policy)
        with mock.patch("sys.stderr"), self.assertRaises(RuntimeError):
            agent.run()


if __name__ == "__main__":
    unittest.main()
