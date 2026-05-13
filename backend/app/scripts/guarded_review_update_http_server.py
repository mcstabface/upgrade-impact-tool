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
from app.scripts.local_policy_auth_adapter import LocalPolicyAuthAdapter
from app.scripts.review_authorization import provenance_from_headers
from app.scripts.review_update_service import request_from_json
from app.scripts.security_denial_audit import append_security_denial_event


ALLOWED_BROWSER_ORIGINS = {"null", "http://127.0.0.1:8766", "http://localhost:8766"}


def append_endpoint_denial(
    *,
    audit_path: Path,
    request_id: str,
    route: str,
    action: str,
    target_id: str,
    reviewer_id: str,
    principal_subject: str,
    principal_issuer: str,
    denial_reason: str,
    source: str,
    user_agent: str,
) -> None:
    append_security_denial_event(
        audit_path=audit_path,
        request_id=request_id or "MISSING_REQUEST_ID",
        route=route,
        action=action or "UNKNOWN_ACTION",
        target_id=target_id or "UNKNOWN_TARGET",
        reviewer_id=reviewer_id or "UNKNOWN_REVIEWER",
        principal_subject=principal_subject or reviewer_id or "UNKNOWN_PRINCIPAL",
        principal_issuer=principal_issuer or "local-policy",
        denial_reason=denial_reason,
        source=source or "UNKNOWN_SOURCE",
        user_agent=user_agent or "UNKNOWN_USER_AGENT",
    )


class AuditedPermissionError(PermissionError):
    """PermissionError marker for denials already written to security audit."""


class GuardedReviewUpdateHTTPHandler(BaseHTTPRequestHandler):
    server_version = "KBGuardedReviewUpdateHTTP/1.1"

    def _send_browser_scaffold_headers(self) -> None:
        """Allow the local Gate 17 browser scaffold to call the guarded endpoint.

        This is intentionally narrow and does not use credentials. A static file opened
        directly in a browser sends Origin: null, so that origin is allowed for local
        smoke/demo use only.
        """
        origin = self.headers.get("Origin", "")
        if origin in ALLOWED_BROWSER_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept, X-Request-Id, X-Review-Source")
        self.send_header("Access-Control-Max-Age", "600")

    def _json_response(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_browser_scaffold_headers()
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

    def do_OPTIONS(self) -> None:  # noqa: N802 - stdlib handler API
        route = urlparse(self.path).path
        if route not in {"/health", "/review/update"}:
            self._json_response(HTTPStatus.NOT_FOUND, {"status": "ERROR", "error": f"Unknown route: {route}"})
            return
        self.send_response(HTTPStatus.NO_CONTENT.value)
        self._send_browser_scaffold_headers()
        self.end_headers()

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
                    "security_denial_audit_enabled": True,
                    "browser_action_scaffold_allowed": True,
                    "finalization_allowed": False,
                    "mutation_contract": "Gate 13 ReviewUpdateRequest + Gate 16B auth adapter",
                },
            )
            return
        self._json_response(HTTPStatus.NOT_FOUND, {"status": "ERROR", "error": f"Unknown route: {route}"})

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        route = urlparse(self.path).path
        if route != "/review/update":
            self._json_response(HTTPStatus.NOT_FOUND, {"status": "ERROR", "error": f"Unknown route: {route}"})
            return

        request_id = self.headers.get("X-Request-Id", "")
        source = self.headers.get("X-Review-Source", "HTTP")
        user_agent = self.headers.get("User-Agent", "")
        reviewer_id = ""
        action = ""
        target_id = ""
        principal_subject = ""
        principal_issuer = "local-policy"

        try:
            payload = self._read_json_body()
            request = request_from_json(payload)
            reviewer_id = request.reviewer
            action = request.action
            target_id = request.target_id

            adapter = LocalPolicyAuthAdapter(self.server.policy_path)  # type: ignore[attr-defined]
            try:
                decision = adapter.authorize_request_context({"reviewer_id": reviewer_id}, action=action)
            except PermissionError as exc:
                append_endpoint_denial(
                    audit_path=self.server.security_audit_output,  # type: ignore[attr-defined]
                    request_id=request_id,
                    route=route,
                    action=action,
                    target_id=target_id,
                    reviewer_id=reviewer_id,
                    principal_subject=reviewer_id,
                    principal_issuer=principal_issuer,
                    denial_reason=str(exc),
                    source=source,
                    user_agent=user_agent,
                )
                raise AuditedPermissionError(str(exc)) from exc

            if decision.reviewer_identity is not None:
                principal_subject = decision.reviewer_identity.principal_subject
                principal_issuer = decision.reviewer_identity.principal_issuer
            if not decision.allowed:
                append_endpoint_denial(
                    audit_path=self.server.security_audit_output,  # type: ignore[attr-defined]
                    request_id=request_id,
                    route=route,
                    action=action,
                    target_id=target_id,
                    reviewer_id=reviewer_id,
                    principal_subject=principal_subject,
                    principal_issuer=principal_issuer,
                    denial_reason=decision.reason,
                    source=source,
                    user_agent=user_agent,
                )
                raise AuditedPermissionError(decision.reason)

            try:
                provenance = provenance_from_headers(
                    request_id=request_id,
                    route=route,
                    source=source,
                    user_agent=user_agent,
                    remote_addr=self.client_address[0] if self.client_address else "UNKNOWN_REMOTE_ADDR",
                )
            except Exception as exc:
                append_endpoint_denial(
                    audit_path=self.server.security_audit_output,  # type: ignore[attr-defined]
                    request_id=request_id,
                    route=route,
                    action=action,
                    target_id=target_id,
                    reviewer_id=reviewer_id,
                    principal_subject=principal_subject,
                    principal_issuer=principal_issuer,
                    denial_reason=str(exc),
                    source=source,
                    user_agent=user_agent,
                )
                raise

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
                    "security_denial_audit_enabled": True,
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
                    "security_denial_audit_enabled": True,
                    "finalization_allowed": False,
                },
            )

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[gate16c:http] {self.address_string()} - {format % args}")


def build_server(
    *,
    host: str,
    port: int,
    policy_path: Path,
    manifest_path: Path,
    export_output: Path,
    surface_output: Path,
    security_audit_output: Path,
) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), GuardedReviewUpdateHTTPHandler)
    server.policy_path = policy_path  # type: ignore[attr-defined]
    server.manifest_path = manifest_path  # type: ignore[attr-defined]
    server.export_output = export_output  # type: ignore[attr-defined]
    server.surface_output = surface_output  # type: ignore[attr-defined]
    server.security_audit_output = security_audit_output  # type: ignore[attr-defined]
    return server


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run a local Gate 16C guarded KB review update HTTP endpoint.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--policy", type=Path, default=root / "kbs" / "policies" / "review_authorization_policy.v1.json")
    parser.add_argument("--manifest", type=Path, default=root / "kbs" / "review" / "kb_draft_review_manifest.v1.json")
    parser.add_argument("--export-output", type=Path, default=root / "kbs" / "manifests" / "kb_draft_review_export.md")
    parser.add_argument("--surface-output", type=Path, default=root / "kbs" / "manifests" / "kb_draft_review_surface.html")
    parser.add_argument("--security-audit-output", type=Path, default=root / "kbs" / "audit" / "security_denials.jsonl")
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
        security_audit_output=args.security_audit_output,
    )
    print(f"[gate16c:http] Serving guarded KB review update endpoint on http://{args.host}:{args.port}")
    print("[gate16c:http] Routes: GET /health, POST /review/update")
    print(f"[gate16c:http] Policy: {args.policy}")
    print(f"[gate16c:http] Manifest: {args.manifest}")
    print(f"[gate16c:http] Security audit: {args.security_audit_output}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[gate16c:http] Shutting down")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
