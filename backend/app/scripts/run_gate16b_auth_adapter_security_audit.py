from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.local_policy_auth_adapter import LocalPolicyAuthAdapter
from app.scripts.security_denial_audit import append_security_denial_event


ROOT = repo_root()
AUDIT_PATH = ROOT / "kbs" / "audit" / "security_denials.gate16b.jsonl"


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate16b]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def smoke_adapter_and_audit(*, dry_run: bool) -> None:
    print("[gate16b] Smoke local policy auth adapter")
    if dry_run:
        print("[gate16b]   would authorize reviewer and deny observer/unknown reviewer")
        return

    if AUDIT_PATH.exists():
        AUDIT_PATH.unlink()

    adapter = LocalPolicyAuthAdapter()

    allowed = adapter.authorize_request_context({"reviewer_id": "GATE15_AUTH_SMOKE"}, action="claim")
    if not allowed.allowed:
        raise SystemExit(f"Expected authorized reviewer to be allowed: {allowed}")
    if allowed.reviewer_identity is None or allowed.reviewer_identity.principal_issuer != "local-policy":
        raise SystemExit(f"Expected principal-derived reviewer identity from local policy: {allowed}")

    denied = adapter.authorize_request_context({"reviewer_id": "GATE15_OBSERVER_SMOKE"}, action="gap")
    if denied.allowed:
        raise SystemExit(f"Expected observer to be denied: {denied}")
    append_security_denial_event(
        audit_path=AUDIT_PATH,
        request_id="gate16b-request-0001",
        route="/review/update",
        action="gap",
        target_id="gap_001",
        reviewer_id="GATE15_OBSERVER_SMOKE",
        principal_subject=(denied.reviewer_identity.principal_subject if denied.reviewer_identity else "GATE15_OBSERVER_SMOKE"),
        principal_issuer=(denied.reviewer_identity.principal_issuer if denied.reviewer_identity else "local-policy"),
        denial_reason=denied.reason,
        source="gate16b-auth-adapter-smoke",
        user_agent="gate16b-smoke-runner",
    )

    try:
        adapter.authorize_request_context({"reviewer_id": "UNKNOWN_REVIEWER"}, action="claim")
    except PermissionError as exc:
        append_security_denial_event(
            audit_path=AUDIT_PATH,
            request_id="gate16b-request-0002",
            route="/review/update",
            action="claim",
            target_id="evidence_group_006",
            reviewer_id="UNKNOWN_REVIEWER",
            principal_subject="UNKNOWN_REVIEWER",
            principal_issuer="local-policy",
            denial_reason=str(exc),
            source="gate16b-auth-adapter-smoke",
            user_agent="gate16b-smoke-runner",
        )
    else:
        raise SystemExit("Expected unknown reviewer to raise PermissionError.")

    print(f"[gate16b] Wrote security denial audit: {AUDIT_PATH}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gate 16B auth adapter and security denial audit smoke checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print("[gate16b] Starting auth adapter / security audit pipeline")
    print(f"[gate16b] Repository root: {ROOT}")
    smoke_adapter_and_audit(dry_run=args.dry_run)
    run_module(
        "app.scripts.validate_security_denial_audit",
        ["--audit", str(AUDIT_PATH), "--min-events", "2"],
        dry_run=args.dry_run,
    )
    if args.dry_run:
        print("[gate16b] Dry run complete")
        return
    if not AUDIT_PATH.exists():
        raise SystemExit(f"Expected audit output missing: {AUDIT_PATH}")
    print("[gate16b] Pipeline complete")
    print(f"[gate16b] Output: {AUDIT_PATH}")


if __name__ == "__main__":
    main()
