from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlopen

from app.scripts.extract_kb_source_manifest import repo_root


@dataclass(frozen=True)
class PipelineStep:
    label: str
    module: str
    args: list[str]


ROOT = repo_root()
REVIEW_ROOT = ROOT / "kbs" / "review"
MANIFEST_ROOT = ROOT / "kbs" / "manifests"
BASE_MANIFEST = REVIEW_ROOT / "kb_draft_review_manifest.v1.json"
HTTP_MANIFEST = REVIEW_ROOT / "kb_draft_review_manifest.gate14_http.json"
HTTP_EXPORT = MANIFEST_ROOT / "kb_draft_review_export.gate14_http.md"
HTTP_SURFACE = MANIFEST_ROOT / "kb_draft_review_surface.gate14_http.html"
CLAIM_RESPONSE = REVIEW_ROOT / "gate14_claim_response.json"
GAP_RESPONSE = REVIEW_ROOT / "gate14_gap_response.json"

EXPECTED_OUTPUTS = [
    "kbs/review/kb_draft_review_manifest.gate14_http.json",
    "kbs/review/gate14_claim_response.json",
    "kbs/review/gate14_gap_response.json",
    "kbs/manifests/kb_draft_review_export.gate14_http.md",
    "kbs/manifests/kb_draft_review_surface.gate14_http.html",
]


def wait_for_health(base_url: str, *, timeout_seconds: int = 15) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urlopen(f"{base_url}/health", timeout=2) as response:  # noqa: S310 - local smoke check only
                if response.status == 200:
                    return
        except Exception as exc:  # wait for subprocess server startup
            last_error = exc
            time.sleep(0.25)
    raise RuntimeError(f"Timed out waiting for Gate 14 HTTP endpoint health check: {last_error}")


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate14]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_outputs(repository_root: Path) -> list[str]:
    missing: list[str] = []
    for output in EXPECTED_OUTPUTS:
        if not (repository_root / output).exists():
            missing.append(output)
    return missing


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gate 14 local KB review update HTTP endpoint smoke checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()
    base_url = f"http://{args.host}:{args.port}"

    print("[gate14] Starting KB review HTTP endpoint pipeline")
    print(f"[gate14] Repository root: {repository_root}")

    print("[gate14] Run Gate 11 read-only review surface pipeline")
    run_module("app.scripts.run_gate11_kb_review_surface", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate14] Would copy base manifest to HTTP smoke manifest")
        print("[gate14] Would start local HTTP server, run smoke client, validate outputs, and stop server")
        print("[gate14] Dry run complete")
        return

    REVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST_ROOT.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(BASE_MANIFEST, HTTP_MANIFEST)
    print(f"[gate14] Copied base manifest to HTTP manifest: {HTTP_MANIFEST}")

    server_command = [
        sys.executable,
        "-m",
        "app.scripts.review_update_http_server",
        "--host",
        args.host,
        "--port",
        str(args.port),
        "--manifest",
        str(HTTP_MANIFEST),
        "--export-output",
        str(HTTP_EXPORT),
        "--surface-output",
        str(HTTP_SURFACE),
    ]
    print(f"[gate14] Starting server: {' '.join(server_command)}")
    server = subprocess.Popen(server_command)
    try:
        wait_for_health(base_url)
        print("[gate14] HTTP endpoint health check OK")
        run_module(
            "app.scripts.smoke_kb_review_update_http_endpoint",
            [
                "--base-url",
                base_url,
                "--claim-response-output",
                str(CLAIM_RESPONSE),
                "--gap-response-output",
                str(GAP_RESPONSE),
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
        print("[gate14] HTTP endpoint stopped")

    print("[gate14] Validate HTTP mutable review state")
    run_module("app.scripts.validate_kb_review_state", ["--manifest", str(HTTP_MANIFEST)], dry_run=False)
    print("[gate14] Validate HTTP audit trail")
    run_module("app.scripts.validate_kb_review_audit_trail", ["--manifest", str(HTTP_MANIFEST), "--min-events", "2"], dry_run=False)
    print("[gate14] Validate HTTP regenerated read-only surface")
    run_module("app.scripts.validate_kb_draft_review_surface", ["--surface", str(HTTP_SURFACE)], dry_run=False)
    print("[gate14] Validate HTTP claim response")
    run_module(
        "app.scripts.validate_kb_review_update_service_response",
        [str(CLAIM_RESPONSE), "--expected-action", "claim", "--expected-target-id", "evidence_group_006", "--min-audit-events", "1"],
        dry_run=False,
    )
    print("[gate14] Validate HTTP gap response")
    run_module(
        "app.scripts.validate_kb_review_update_service_response",
        [str(GAP_RESPONSE), "--expected-action", "gap", "--expected-target-id", "gap_001", "--min-audit-events", "2"],
        dry_run=False,
    )

    missing_outputs = verify_outputs(repository_root)
    if missing_outputs:
        print("[gate14] Pipeline completed, but expected outputs are missing:")
        for output in missing_outputs:
            print(f"[gate14]   missing: {output}")
        raise SystemExit(1)

    print("[gate14] Pipeline complete")
    print("[gate14] Outputs:")
    for output in EXPECTED_OUTPUTS:
        print(f"[gate14]   {output}")


if __name__ == "__main__":
    main()
