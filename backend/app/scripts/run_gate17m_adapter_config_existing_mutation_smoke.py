from __future__ import annotations

import argparse
import json
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
POLICY_ROOT = ROOT / "kbs" / "policies"
POLICY = POLICY_ROOT / "review_authorization_policy.v1.json"
BASE_MANIFEST = REVIEW_ROOT / "kb_draft_review_manifest.v1.json"
SMOKE_MANIFEST = REVIEW_ROOT / "kb_draft_review_manifest.gate17m_adapter_config.json"
SMOKE_EXPORT = MANIFEST_ROOT / "kb_draft_review_export.gate17m_adapter_config.md"
SMOKE_SURFACE = MANIFEST_ROOT / "kb_draft_review_surface.gate17m_adapter_config.html"
SECURITY_AUDIT = AUDIT_ROOT / "security_denials.gate17m.jsonl"
ADAPTER_CONFIG = POLICY_ROOT / "review_endpoint_auth_adapter.gate17m.config.json"
AUTHORIZED_RESPONSE = REVIEW_ROOT / "gate17m_authorized_response.json"
DENIED_RESPONSE = REVIEW_ROOT / "gate17m_denied_response.json"
MISSING_PROVENANCE_RESPONSE = REVIEW_ROOT / "gate17m_missing_provenance_response.json"

EXPECTED_OUTPUTS = [
    "kbs/review/kb_draft_review_manifest.gate17m_adapter_config.json",
    "kbs/review/gate17m_authorized_response.json",
    "kbs/review/gate17m_denied_response.json",
    "kbs/review/gate17m_missing_provenance_response.json",
    "kbs/manifests/kb_draft_review_export.gate17m_adapter_config.md",
    "kbs/manifests/kb_draft_review_surface.gate17m_adapter_config.html",
    "kbs/audit/security_denials.gate17m.jsonl",
    "kbs/policies/review_endpoint_auth_adapter.gate17m.config.json",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate17m]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def wait_for_health(base_url: str, *, timeout_seconds: int = 15) -> dict[str, object]:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urlopen(f"{base_url}/health", timeout=2) as response:  # noqa: S310 - local smoke check only
                if response.status == 200:
                    return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            last_error = exc
            time.sleep(0.25)
    raise RuntimeError(f"Timed out waiting for Gate 17M guarded HTTP endpoint health check: {last_error}")


def write_adapter_config(path: Path) -> None:
    payload = {
        "review_update_auth_adapter": "oidc",
        "allow_oidc_adapter": True,
        "oidc_config_path": "kbs/policies/review_oidc_adapter.config.json",
        "local_policy_path": "kbs/policies/review_authorization_policy.v1.json",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_health_is_config_visible_but_local_policy_live(health: dict[str, object]) -> None:
    adapter_config = health.get("adapter_config")
    if not isinstance(adapter_config, dict):
        raise AssertionError(f"Health payload missing adapter_config: {health}")
    if adapter_config.get("configured_adapter") != "oidc":
        raise AssertionError(f"Expected configured adapter oidc, got: {adapter_config}")
    if adapter_config.get("allow_oidc_adapter") is not True:
        raise AssertionError(f"Expected allow_oidc_adapter true, got: {adapter_config}")
    if adapter_config.get("endpoint_integration_allowed") is not False:
        raise AssertionError(f"Endpoint integration must remain disabled, got: {adapter_config}")
    if adapter_config.get("live_adapter") != "local_policy":
        raise AssertionError(f"Live adapter must remain local_policy, got: {adapter_config}")
    if health.get("adapter_config_health_only") is not True:
        raise AssertionError(f"Health must mark adapter config as health-only, got: {health}")
    if health.get("finalization_allowed") is not False:
        raise AssertionError(f"Finalization must remain disabled, got: {health}")


def verify_outputs(repository_root: Path) -> list[str]:
    return [output for output in EXPECTED_OUTPUTS if not (repository_root / output).exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gate 17M guarded endpoint smoke with adapter config health surface.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()
    base_url = f"http://{args.host}:{args.port}"

    print("[gate17m] Starting adapter config existing mutation smoke pipeline")
    print(f"[gate17m] Repository root: {repository_root}")

    print("[gate17m] Run Gate 11 read-only review surface pipeline")
    run_module("app.scripts.run_gate11_kb_review_surface", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate17m] Would write adapter config, start guarded server, check health, run existing mutation smoke, validate artifacts")
        print("[gate17m] Dry run complete")
        return

    REVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST_ROOT.mkdir(parents=True, exist_ok=True)
    AUDIT_ROOT.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(BASE_MANIFEST, SMOKE_MANIFEST)
    write_adapter_config(ADAPTER_CONFIG)
    if SECURITY_AUDIT.exists():
        SECURITY_AUDIT.unlink()

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
        str(SMOKE_MANIFEST),
        "--export-output",
        str(SMOKE_EXPORT),
        "--surface-output",
        str(SMOKE_SURFACE),
        "--security-audit-output",
        str(SECURITY_AUDIT),
        "--adapter-config",
        str(ADAPTER_CONFIG),
    ]
    print(f"[gate17m] Starting guarded server: {' '.join(server_command)}")
    server = subprocess.Popen(server_command)
    try:
        health = wait_for_health(base_url)
        assert_health_is_config_visible_but_local_policy_live(health)
        print("[gate17m] Guarded HTTP endpoint health check OK with adapter config health-only payload")
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
        print("[gate17m] Guarded HTTP endpoint stopped")

    print("[gate17m] Validate guarded mutable review state")
    run_module("app.scripts.validate_kb_review_state", ["--manifest", str(SMOKE_MANIFEST)], dry_run=False)
    print("[gate17m] Validate guarded mutation audit trail")
    run_module("app.scripts.validate_kb_review_audit_trail", ["--manifest", str(SMOKE_MANIFEST), "--min-events", "1"], dry_run=False)
    print("[gate17m] Validate guarded provenance")
    run_module("app.scripts.validate_kb_review_provenance", ["--manifest", str(SMOKE_MANIFEST), "--min-events", "1"], dry_run=False)
    print("[gate17m] Validate endpoint security denial audit")
    run_module("app.scripts.validate_security_denial_audit", ["--audit", str(SECURITY_AUDIT), "--min-events", "2"], dry_run=False)
    print("[gate17m] Validate guarded regenerated read-only surface")
    run_module("app.scripts.validate_kb_draft_review_surface", ["--surface", str(SMOKE_SURFACE)], dry_run=False)

    missing_outputs = verify_outputs(repository_root)
    if missing_outputs:
        print("[gate17m] Pipeline completed, but expected outputs are missing:")
        for output in missing_outputs:
            print(f"[gate17m]   missing: {output}")
        raise SystemExit(1)

    print("[gate17m] Pipeline complete")
    print("[gate17m] Adapter config health surface coexists with existing local-policy mutation path")


if __name__ == "__main__":
    main()
