from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.scripts.extract_kb_source_manifest import repo_root


def http_json(method: str, url: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=body, method=method, headers=headers)
    try:
        with urlopen(request, timeout=10) as response:  # noqa: S310 - local smoke client only
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_ok_response(response: dict[str, Any], *, action: str, target_id: str, min_audit_events: int) -> None:
    if response.get("status") != "OK":
        raise ValueError(f"Expected OK response, got: {response}")
    if response.get("action") != action:
        raise ValueError(f"Expected action={action!r}, got {response.get('action')!r}")
    if response.get("target_id") != target_id:
        raise ValueError(f"Expected target_id={target_id!r}, got {response.get('target_id')!r}")
    if int(response.get("audit_event_count") or 0) < min_audit_events:
        raise ValueError(f"Expected at least {min_audit_events} audit events, got {response.get('audit_event_count')!r}")
    if response.get("review_status") != "IN_REVIEW":
        raise ValueError(f"Expected review_status='IN_REVIEW', got {response.get('review_status')!r}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Smoke test the local Gate 14 KB review update HTTP endpoint.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    parser.add_argument("--claim-response-output", type=Path, default=root / "kbs" / "review" / "gate14_claim_response.json")
    parser.add_argument("--gap-response-output", type=Path, default=root / "kbs" / "review" / "gate14_gap_response.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    health_status, health = http_json("GET", f"{args.base_url}/health")
    if health_status != 200 or health.get("status") != "OK":
        raise SystemExit(f"Health check failed: status={health_status} response={health}")
    if health.get("finalization_allowed") is not False:
        raise SystemExit(f"Health check must report finalization_allowed=false: {health}")

    claim_payload = {
        "action": "claim",
        "target_id": "evidence_group_006",
        "value": "ACCEPT",
        "reviewer": "GATE14_HTTP_SMOKE",
        "notes": "HTTP smoke-test acceptance with visual acknowledgement.",
        "visual_acknowledged": True,
    }
    claim_status, claim_response = http_json("POST", f"{args.base_url}/review/update", claim_payload)
    if claim_status != 200:
        raise SystemExit(f"Claim update failed: status={claim_status} response={claim_response}")
    validate_ok_response(claim_response, action="claim", target_id="evidence_group_006", min_audit_events=1)
    write_json(args.claim_response_output, claim_response)

    gap_payload = {
        "action": "gap",
        "target_id": "gap_001",
        "value": "ACKNOWLEDGED",
        "reviewer": "GATE14_HTTP_SMOKE",
        "notes": "HTTP smoke-test unresolved gap acknowledgement.",
    }
    gap_status, gap_response = http_json("POST", f"{args.base_url}/review/update", gap_payload)
    if gap_status != 200:
        raise SystemExit(f"Gap update failed: status={gap_status} response={gap_response}")
    validate_ok_response(gap_response, action="gap", target_id="gap_001", min_audit_events=2)
    write_json(args.gap_response_output, gap_response)

    print("[gate14:http-smoke] OK")
    print(f"[gate14:http-smoke] claim_response={args.claim_response_output}")
    print(f"[gate14:http-smoke] gap_response={args.gap_response_output}")


if __name__ == "__main__":
    main()
