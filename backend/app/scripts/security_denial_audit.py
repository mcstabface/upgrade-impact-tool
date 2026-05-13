from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


@dataclass(frozen=True)
class SecurityDenialAuditEvent:
    event_id: str
    timestamp_utc: str
    event_type: str
    request_id: str
    route: str
    action: str
    target_id: str
    reviewer_id: str
    principal_subject: str
    principal_issuer: str
    decision: str
    denial_reason: str
    source: str
    user_agent: str
    finalization_allowed: bool
    previous_hash: str
    event_hash: str


def default_audit_path() -> Path:
    return repo_root() / "kbs" / "audit" / "security_denials.jsonl"


def latest_event_hash(path: Path) -> str:
    if not path.exists():
        return "GENESIS"
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return "GENESIS"
    try:
        latest = json.loads(lines[-1])
    except json.JSONDecodeError:
        return "CORRUPT_PREVIOUS_EVENT"
    return str(latest.get("event_hash") or "UNKNOWN_PREVIOUS_HASH")


def compute_event_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def append_security_denial_event(
    *,
    audit_path: Path | None = None,
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
) -> SecurityDenialAuditEvent:
    path = audit_path or default_audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    previous_hash = latest_event_hash(path)
    existing_count = 0
    if path.exists():
        existing_count = len([line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()])

    base_payload = {
        "event_id": f"security_denial_{existing_count + 1:04d}",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "event_type": "SECURITY_DENIAL",
        "request_id": request_id,
        "route": route,
        "action": action,
        "target_id": target_id,
        "reviewer_id": reviewer_id,
        "principal_subject": principal_subject,
        "principal_issuer": principal_issuer,
        "decision": "DENIED",
        "denial_reason": denial_reason,
        "source": source,
        "user_agent": user_agent,
        "finalization_allowed": False,
        "previous_hash": previous_hash,
    }
    event_hash = compute_event_hash(base_payload)
    event = SecurityDenialAuditEvent(**base_payload, event_hash=event_hash)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(event), sort_keys=True) + "\n")
    return event
