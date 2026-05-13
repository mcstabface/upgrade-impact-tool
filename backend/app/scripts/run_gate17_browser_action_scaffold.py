from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


ROOT = repo_root()
REVIEW_ROOT = ROOT / "kbs" / "review"
MANIFEST_ROOT = ROOT / "kbs" / "manifests"
BASE_MANIFEST = REVIEW_ROOT / "kb_draft_review_manifest.v1.json"
GATE17_MANIFEST = REVIEW_ROOT / "kb_draft_review_manifest.gate17_browser.json"
GATE17_SCAFFOLD = MANIFEST_ROOT / "kb_draft_review_action_scaffold.gate17.html"

EXPECTED_OUTPUTS = [
    "kbs/review/kb_draft_review_manifest.gate17_browser.json",
    "kbs/manifests/kb_draft_review_action_scaffold.gate17.html",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate17]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_outputs(repository_root: Path) -> list[str]:
    return [output for output in EXPECTED_OUTPUTS if not (repository_root / output).exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gate 17 browser action scaffold generation and validation.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument("--endpoint-url", default="http://127.0.0.1:8766/review/update")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate17] Starting browser action scaffold pipeline")
    print(f"[gate17] Repository root: {repository_root}")

    print("[gate17] Run Gate 11 read-only review surface pipeline")
    run_module("app.scripts.run_gate11_kb_review_surface", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate17] Would copy base manifest to Gate 17 browser scaffold manifest")
        print("[gate17] Would write and validate browser action scaffold")
        print("[gate17] Dry run complete")
        return

    REVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST_ROOT.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(BASE_MANIFEST, GATE17_MANIFEST)
    print(f"[gate17] Copied base manifest to browser scaffold manifest: {GATE17_MANIFEST}")

    print("[gate17] Write browser action scaffold")
    run_module(
        "app.scripts.write_gate17_browser_action_scaffold",
        ["--manifest", str(GATE17_MANIFEST), "--output", str(GATE17_SCAFFOLD), "--endpoint-url", args.endpoint_url],
        dry_run=False,
    )

    print("[gate17] Validate browser action scaffold")
    run_module("app.scripts.validate_gate17_browser_action_scaffold", ["--scaffold", str(GATE17_SCAFFOLD)], dry_run=False)

    missing_outputs = verify_outputs(repository_root)
    if missing_outputs:
        print("[gate17] Pipeline completed, but expected outputs are missing:")
        for output in missing_outputs:
            print(f"[gate17]   missing: {output}")
        raise SystemExit(1)

    print("[gate17] Pipeline complete")
    print("[gate17] Outputs:")
    for output in EXPECTED_OUTPUTS:
        print(f"[gate17]   {output}")
    print("[gate17] Manual local browser smoke:")
    print("[gate17]   1. Start app.scripts.guarded_review_update_http_server with matching --manifest/--surface-output paths.")
    print(f"[gate17]   2. Open {GATE17_SCAFFOLD} in a browser.")
    print("[gate17]   3. Submit only through POST /review/update; never edit review JSON directly.")


if __name__ == "__main__":
    main()
