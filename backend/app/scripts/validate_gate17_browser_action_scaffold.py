from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


@dataclass(frozen=True)
class ValidationFailure:
    check: str
    detail: str


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return path.read_text(encoding="utf-8")


def validate_scaffold(path: Path) -> list[ValidationFailure]:
    html = read_text(path)
    failures: list[ValidationFailure] = []

    required_fragments = [
        "Gate 17 Browser Action Scaffold",
        "POST /review/update",
        "No direct JSON mutation",
        "Authorization, provenance, mutation audit, security-denial audit",
        "Finalization remains disabled",
        "X-Request-Id",
        "X-Review-Source",
        "gate17-browser-action-scaffold",
        "visual_acknowledged",
        "fetch(endpointUrl",
        "POST guarded review update",
    ]
    for fragment in required_fragments:
        if fragment not in html:
            failures.append(ValidationFailure("required_fragment", f"Missing required fragment: {fragment!r}."))

    forbidden_fragments = [
        "kb_draft_review_manifest.v1.json",
        "FileSystemWritableFileStream",
        "showSaveFilePicker",
        "localStorage",
        "sessionStorage",
        "finalize",
        "FINALIZE",
    ]
    for fragment in forbidden_fragments:
        if fragment in html:
            failures.append(ValidationFailure("forbidden_fragment", f"Forbidden scaffold fragment found: {fragment!r}."))

    if html.count("<form") != 1:
        failures.append(ValidationFailure("form_count", "Expected exactly one browser action form."))
    if html.count("fetch(") != 1:
        failures.append(ValidationFailure("endpoint_call_count", "Expected exactly one fetch call to the guarded endpoint."))
    if "method: 'POST'" not in html and 'method: "POST"' not in html:
        failures.append(ValidationFailure("post_only", "Expected fetch request to use POST."))
    if "enable-post" not in html or "submitEl.disabled = !enableEl.checked" not in html:
        failures.append(ValidationFailure("explicit_enable_gate", "Expected explicit checkbox gate before POST is enabled."))

    return failures


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 17 browser action scaffold HTML.")
    parser.add_argument("--scaffold", type=Path, default=root / "kbs" / "manifests" / "kb_draft_review_action_scaffold.gate17.html")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures = validate_scaffold(args.scaffold)
    if failures:
        print("[gate17:validate] FAILED")
        for failure in failures:
            print(f"[gate17:validate] {failure.check}: {failure.detail}")
        raise SystemExit(1)
    print("[gate17:validate] OK")
    print(f"[gate17:validate] scaffold={args.scaffold}")


if __name__ == "__main__":
    main()
