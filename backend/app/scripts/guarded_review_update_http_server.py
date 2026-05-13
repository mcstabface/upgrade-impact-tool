from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.guarded_review_update_service import apply_guarded_review_update_request, guarded_response_to_dict
from app.scripts.review_authorization import provenance_from_headers
from app.scripts.review_update_service import request_from_json


class GuardedReviewUpdateHTTPHandler(BaseHTTPRequestHandler):
    server_version = "KBGuardedReviewUpdateHTTP/1.0"

    def _json_response(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length") or "0")
        if content_length <= 0:
            raise ValueError("Request body is required.")
        payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("JSON request body must be an object.")
        return payload

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        route = urlparse(self.path).path
        if route == "/health":
            self._json_response(
                HTTPStatus.OK,
                {
                    "status": "OK",
                    "service": "kb_guarded_review_update",
                    "authorization_required": True,
                    "provenance_required": True,
                    "finalization_allowed": False,
                    "mutation_contract": "Gate 13 ReviewUpdateRequest + Gate 15 reviewer authorization",
                },
            )
            return
        self._json_response(HTTPStatus.NOT_FOUND, {"status": "ERROR", "error": f"Unknown route: {route}"})

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        route = urlparse(self.path).path
        if route != "/review/update":
            self._json_response(HTTPStatus.NOT_FOUND, {"status": "ERROR", "error": f"Unknown route: {route}"})
            return
        try:
            payload = self._read_json_body()
            request = request_from_json(payload)
            request_id = self.headers.get("X-Request-Id", "")
            provenance = provenance_from_headers(
                request_id=request_id,
                route=route,
                source=self.headers.get("X-Review-Source", "HTTP"),
                user_agent=self.headers.get("User-Agent", ""),
                remote_addr=self.client_address[0] if self.client_address else "UNKNOWN_REMOTE_ADDR",
            )
            response = apply_guarded_review_update_request(
                request,
                provenance=provenance,
                policy_path=self.server.policy_path,  # type: ignore[attr-defined]
                manifest_path=self.server.manifest_path,  # type: ignore[attr-defined]
                output_path=self.server.manifest_path,  # type: ignore[attr-defined]
                export_path=self.server.export_output,  # type: ignore[attr-defined]
                surface_path=self.server.surface_output,  # type: ignore[attr-defined]
            )
            self._json_response(HTTPStatus.OK, guarded_response_to_dict(response))
        except PermissionError as exc:
            self._json_response(
                HTTPStatus.FORBIDDEN,
                {
                    "status": "ERROR",
                    "authorization_status": "DENIED",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "finalization_allowed": False,
                },
            )
        except Exception as exc:
            self._json_response(
                HTTPStatus.BAD_REQUEST,
                {
                    "status": "ERROR",
                    "authorization_status": "ERROR",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "finalization_allowed": False,
                },
            )

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[gate15:http] {self.address_string()} - {format % args}")


def build_server(
    *,
    host: str,
    port: int,
    policy_path: Path,
    manifest_path: Path,
    export_output: Path,
    surface_output: Path,
) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), GuardedReviewUpdateHTTPHandler)
    server.policy_path = policy_path  # type: ignore[attr-defined]
    server.manifest_path = manifest_path  # type: ignore[attr-defined]
    server.export_output = export_output  # type: ignore[attr-defined]
    server.surface_output = surface_output  # type: ignore[attr-defined]
    return server


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run a local Gate 15 guarded KB review update HTTP endpoint.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--policy", type=Path, default=root / "kbs" / "policies" / "review_authorization_policy.v1.json")
    parser.add_argument("--manifest", type=Path, default=root / "kbs" / "review" / "kb_draft_review_manifest.v1.json")
    parser.add_argument("--export-output", type=Path, default=root / "kbs" / "manifests" / "kb_draft_review_export.md")
    parser.add_argument("--surface-output", type=Path, default=root / "kbs" / "manifests" / "kb_draft_review_surface.html")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = build_server(
        host=args.host,
        port=args.port,
        policy_path=args.policy,
        manifest_path=args.manifest,
        export_output=args.export_output,
        surface_output=args.surface_output,
    )
    print(f"[gate15:http] Serving guarded KB review update endpoint on http://{args.host}:{args.port}")
    print("[gate15:http] Routes: GET /health, POST /review/update")
    print(f"[gate15:http] Policy: {args.policy}")
    print(f"[gate15:http] Manifest: {args.manifest}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[gate15:http] Shutting down")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
