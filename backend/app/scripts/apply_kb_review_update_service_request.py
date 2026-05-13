from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.review_update_service import apply_review_update_request, request_from_json, response_to_json


def read_request(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Request JSON not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Apply a Gate 13 review update service request JSON payload.")
    parser.add_argument("request", type=Path, help="Review update request JSON file.")
    parser.add_argument("--manifest", type=Path, default=root / "kbs" / "review" / "kb_draft_review_manifest.v1.json")
    parser.add_argument("--output", type=Path, help="Output manifest path. Defaults to overwriting --manifest.")
    parser.add_argument("--export-output", type=Path, default=root / "kbs" / "manifests" / "kb_draft_review_export.md")
    parser.add_argument("--surface-output", type=Path, default=root / "kbs" / "manifests" / "kb_draft_review_surface.html")
    parser.add_argument("--response-output", type=Path, help="Optional response JSON output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    request = request_from_json(read_request(args.request))
    response = apply_review_update_request(
        request,
        manifest_path=args.manifest,
        output_path=args.output or args.manifest,
        export_path=args.export_output,
        surface_path=args.surface_output,
    )
    response_json = response_to_json(response)
    if args.response_output:
        args.response_output.parent.mkdir(parents=True, exist_ok=True)
        args.response_output.write_text(response_json, encoding="utf-8")
        print(f"Wrote review update response: {args.response_output}")
    print(response_json.rstrip())


if __name__ == "__main__":
    main()
