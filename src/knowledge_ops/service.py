
from __future__ import annotations

import hmac
import json
import os
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .orchestrator import KnowledgeOpsOrchestrator


class State:
    lock = threading.Lock()
    running = False
    last_error: str | None = None


def _read_json(path: str | Path, default: dict) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


class Handler(BaseHTTPRequestHandler):
    server_version = "KnowledgeOps/1.0"

    def _json(self, status: int, payload: dict) -> None:
        raw = json.dumps(payload, sort_keys=True).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            self._json(HTTPStatus.OK, {"status": "ok"})
            return
        if path == "/ready":
            policy = Path(os.getenv("KNOWLEDGE_OPS_POLICY", "policies/agent-policy.json"))
            config = Path(os.getenv("KNOWLEDGE_OPS_CONFIG", "config/project.json"))
            ready = policy.is_file() and config.is_file()
            self._json(HTTPStatus.OK if ready else HTTPStatus.SERVICE_UNAVAILABLE, {"ready": ready})
            return
        if path == "/metrics":
            self._json(
                HTTPStatus.OK,
                _read_json(os.getenv("KNOWLEDGE_OPS_METRICS", "generated/metrics.json"), {"status": "no_runs"}),
            )
            return
        if path == "/catalog":
            self._json(
                HTTPStatus.OK,
                _read_json(os.getenv("KNOWLEDGE_OPS_CATALOG", "generated/catalog.json"), {"entries": []}),
            )
            return
        self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/run":
            self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        expected = os.getenv("KNOWLEDGE_OPS_RUN_TOKEN")
        supplied = self.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        if not expected or not hmac.compare_digest(supplied, expected):
            self._json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            return
        with State.lock:
            if State.running:
                self._json(HTTPStatus.CONFLICT, {"error": "run_in_progress"})
                return
            State.running = True
        try:
            report = KnowledgeOpsOrchestrator(
                config_path=os.getenv("KNOWLEDGE_OPS_CONFIG", "config/project.json"),
                policy_path=os.getenv("KNOWLEDGE_OPS_POLICY", "policies/agent-policy.json"),
                output_dir=os.getenv("KNOWLEDGE_OPS_OUTPUT", "generated"),
                feedback_path=os.getenv("KNOWLEDGE_OPS_FEEDBACK", "feedback/decisions.jsonl"),
            ).run()
            State.last_error = None
            self._json(HTTPStatus.OK, report.to_dict())
        except Exception as exc:  # keep service alive; never expose credentials
            State.last_error = type(exc).__name__
            self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": type(exc).__name__})
        finally:
            with State.lock:
                State.running = False

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "3000"))
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
