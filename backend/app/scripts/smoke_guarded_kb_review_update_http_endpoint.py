from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.scripts.extract_kb_source_manifest import repo_root


def http_json(method: str, url: str, payload: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    body = None
    request_headers = {"Accept": "application/json", **(headers or {})}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    request = Request(url, data=body, method=method, headers=request_headers)
    try:
        with urlopen(request, timeout=10) as response:  # noqa: S310 - local smoke client only
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Smoke test the local Gate 15 guarded KB review update HTTP endpoint.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8766")
    parser.add_argument("--authorized-response-output", type=Path, default=root / "kbs" / "review" / "gate15_authorized_response.json")
    parser.add_argument("--denied-response-output", type=Path, default=root / "kbs" / "review" / "gate15_denied_response.json")
    parser.add_argument("--missing-provenance-response-output", type=Path, default=root / "kbs" / "review" / "gate15_missing_provenance_response.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    health_status, health = http_json("GET", f"{args.base_url}/health")
    if health_status != 200 or health.get("status") != "OK":
        raise SystemExit(f"Health check failed: status={health_status} response={health}")
    if health.get("authorization_required") is not True or health.get("provenance_required") is not True:
        raise SystemExit(f"Guarded health check must require authorization and provenance: {health}")
    if health.get("finalization_allowed") is not False:
        raise SystemExit(f"Health check must report finalization_allowed=false: {health}")

    authorized_payload = {
        "action": "claim",
        "target_id": "evidence_group_006",
        "value": "ACCEPT",
        "reviewer": "GATE15_AUTH_SMOKE",
        "notes": "Guarded HTTP smoke-test acceptance with visual acknowledgement.",
        "visual_acknowledged": True,
    }
    authorized_status, authorized_response = http_json(
        "POST",
        f"{args.base_url}/review/update",
        authorized_payload,
        headers={"X-Request-Id": "gate15-request-0001", "X-Review-Source": "gate15-http-smoke", "User-Agent": "gate15-smoke-client"},
    )
    if authorized_status != 200 or authorized_response.get("status") != "OK":
        raise SystemExit(f"Authorized update failed: status={authorized_status} response={authorized_response}")
    if authorized_response.get("authorization_status") != "AUTHORIZED":
        raise SystemExit(f"Expected AUTHORIZED response: {authorized_response}")
    if authorized_response.get("reviewer_role") != "reviewer":
        raise SystemExit(f"Expected reviewer role in authorized response: {authorized_response}")
    write_json(args.authorized_response_output, authorized_response)

    denied_payload = {
        "action": "gap",
        "target_id": "gap_001",
        "value": "ACKNOWLEDGED",
        "reviewer": "GATE15_OBSERVER_SMOKE",
        "notes": "Observer should not be allowed to mutate.",
    }
    denied_status, denied_response = http_json(
        "POST",
        f"{args.base_url}/review/update",
        denied_payload,
        headers={"X-Request-Id": "gate15-request-0002", "X-Review-Source": "gate15-http-smoke", "User-Agent": "gate15-smoke-client"},
    )
    if denied_status != 403 or denied_response.get("authorization_status") != "DENIED":
        raise SystemExit(f"Expected observer denial: status={denied_status} response={denied_response}")
    write_json(args.denied_response_output, denied_response)

    missing_provenance_payload = {
        "action": "gap",
        "target_id": "gap_001",
        "value": "ACKNOWLEDGED",
        "reviewer": "GATE15_AUTH_SMOKE",
        "notes": "Missing request ID should be rejected before mutation.",
    }
    missing_status, missing_response = http_json(
        "POST",
        f"{args.base_url}/review/update",
        missing_provenance_payload,
        headers={"X-Review-Source": "gate15-http-smoke", "User-Agent": "gate15-smoke-client"},
    )
    if missing_status != 400 or missing_response.get("authorization_status") != "ERROR":
        raise SystemExit(f"Expected missing provenance rejection: status={missing_status} response={missing_response}")
    write_json(args.missing_provenance_response_output, missing_response)

    print("[gate15:http-smoke] OK")
    print(f"[gate15:http-smoke] authorized_response={args.authorized_response_output}")
    print(f"[gate15:http-smoke] denied_response={args.denied_response_output}")
    print(f"[gate15:http-smoke] missing_provenance_response={args.missing_provenance_response_output}")


if __name__ == "__main__":
    main()
