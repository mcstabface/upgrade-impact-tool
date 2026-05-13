from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

from app.scripts.extract_kb_source_manifest import repo_root


ROOT = repo_root()
REVIEW_ROOT = ROOT / "kbs" / "review"
MANIFEST_ROOT = ROOT / "kbs" / "manifests"
AUDIT_ROOT = ROOT / "kbs" / "audit"
POLICY = ROOT / "kbs" / "policies" / "review_authorization_policy.v1.json"
BASE_MANIFEST = REVIEW_ROOT / "kb_draft_review_manifest.v1.json"
AUTH_MANIFEST = REVIEW_ROOT / "kb_draft_review_manifest.gate16c_auth.json"
AUTH_EXPORT = MANIFEST_ROOT / "kb_draft_review_export.gate16c_auth.md"
AUTH_SURFACE = MANIFEST_ROOT / "kb_draft_review_surface.gate16c_auth.html"
SECURITY_AUDIT = AUDIT_ROOT / "security_denials.gate16c.jsonl"
AUTHORIZED_RESPONSE = REVIEW_ROOT / "gate16c_authorized_response.json"
DENIED_RESPONSE = REVIEW_ROOT / "gate16c_denied_response.json"
MISSING_PROVENANCE_RESPONSE = REVIEW_ROOT / "gate16c_missing_provenance_response.json"

EXPECTED_OUTPUTS = [
    "kbs/review/kb_draft_review_manifest.gate16c_auth.json",
    "kbs/review/gate16c_authorized_response.json",
    "kbs/review/gate16c_denied_response.json",
    "kbs/review/gate16c_missing_provenance_response.json",
    "kbs/manifests/kb_draft_review_export.gate16c_auth.md",
    "kbs/manifests/kb_draft_review_surface.gate16c_auth.html",
    "kbs/audit/security_denials.gate16c.jsonl",
]


def wait_for_health(base_url: str, *, timeout_seconds: int = 15) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urlopen(f"{base_url}/health", timeout=2) as response:  # noqa: S310 - local smoke check only
                if response.status == 200:
                    return
        except Exception as exc:
            last_error = exc
            time.sleep(0.25)
    raise RuntimeError(f"Timed out waiting for Gate 16C guarded HTTP endpoint health check: {last_error}")


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate16c]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_outputs(repository_root: Path) -> list[str]:
    return [output for output in EXPECTED_OUTPUTS if not (repository_root / output).exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gate 16C guarded endpoint security denial audit checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()
    base_url = f"http://{args.host}:{args.port}"

    print("[gate16c] Starting guarded endpoint security audit pipeline")
    print(f"[gate16c] Repository root: {repository_root}")

    print("[gate16c] Run Gate 11 read-only review surface pipeline")
    run_module("app.scripts.run_gate11_kb_review_surface", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate16c] Would copy base manifest to auth smoke manifest")
        print("[gate16c] Would start guarded server with security audit output, run smoke client, validate review/security artifacts, and stop server")
        print("[gate16c] Dry run complete")
        return

    REVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST_ROOT.mkdir(parents=True, exist_ok=True)
    AUDIT_ROOT.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(BASE_MANIFEST, AUTH_MANIFEST)
    if SECURITY_AUDIT.exists():
        SECURITY_AUDIT.unlink()
    print(f"[gate16c] Copied base manifest to auth manifest: {AUTH_MANIFEST}")

    server_command = [
        sys.executable,
        "-m",
        "app.scripts.guarded_review_update_http_server",
        "--host",
        args.host,
        "--port",
        str(args.port),
        "--policy",
        str(POLICY),
        "--manifest",
        str(AUTH_MANIFEST),
        "--export-output",
        str(AUTH_EXPORT),
        "--surface-output",
        str(AUTH_SURFACE),
        "--security-audit-output",
        str(SECURITY_AUDIT),
    ]
    print(f"[gate16c] Starting guarded server: {' '.join(server_command)}")
    server = subprocess.Popen(server_command)
    try:
        wait_for_health(base_url)
        print("[gate16c] Guarded HTTP endpoint health check OK")
        run_module(
            "app.scripts.smoke_guarded_kb_review_update_http_endpoint",
            [
                "--base-url",
                base_url,
                "--authorized-response-output",
                str(AUTHORIZED_RESPONSE),
                "--denied-response-output",
                str(DENIED_RESPONSE),
                "--missing-provenance-response-output",
                str(MISSING_PROVENANCE_RESPONSE),
            ],
            dry_run=False,
        )
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)
        print("[gate16c] Guarded HTTP endpoint stopped")

    print("[gate16c] Validate guarded mutable review state")
    run_module("app.scripts.validate_kb_review_state", ["--manifest", str(AUTH_MANIFEST)], dry_run=False)
    print("[gate16c] Validate guarded mutation audit trail")
    run_module("app.scripts.validate_kb_review_audit_trail", ["--manifest", str(AUTH_MANIFEST), "--min-events", "1"], dry_run=False)
    print("[gate16c] Validate guarded provenance")
    run_module("app.scripts.validate_kb_review_provenance", ["--manifest", str(AUTH_MANIFEST), "--min-events", "1"], dry_run=False)
    print("[gate16c] Validate endpoint security denial audit")
    run_module("app.scripts.validate_security_denial_audit", ["--audit", str(SECURITY_AUDIT), "--min-events", "2"], dry_run=False)
    print("[gate16c] Validate guarded regenerated read-only surface")
    run_module("app.scripts.validate_kb_draft_review_surface", ["--surface", str(AUTH_SURFACE)], dry_run=False)

    missing_outputs = verify_outputs(repository_root)
    if missing_outputs:
        print("[gate16c] Pipeline completed, but expected outputs are missing:")
        for output in missing_outputs:
            print(f"[gate16c]   missing: {output}")
        raise SystemExit(1)

    print("[gate16c] Pipeline complete")
    print("[gate16c] Outputs:")
    for output in EXPECTED_OUTPUTS:
        print(f"[gate16c]   {output}")


if __name__ == "__main__":
    main()
