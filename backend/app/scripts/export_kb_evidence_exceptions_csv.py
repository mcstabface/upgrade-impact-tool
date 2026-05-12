from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root

CSV_COLUMNS = [
    "severity",
    "mapping_status",
    "kb_document_id",
    "maintenance_pack",
    "hot_fix_release_label",
    "about_window_file",
    "bug_patch_number",
    "product",
    "category",
    "description",
    "source_html",
    "evidence_attachment_count",
    "placeholder_attachment_count",
    "evidence_attachment_paths",
    "placeholder_attachment_paths",
    "mapping_warnings",
    "kb_extraction_warnings",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def flatten_list(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, list):
        return " | ".join(str(item) for item in value)
    return str(value)


def iter_exception_rows(summary: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for document in summary.get("documents", []):
        for exception in document.get("exceptions", []):
            rows.append(
                {
                    "severity": str(exception.get("severity") or ""),
                    "mapping_status": str(exception.get("mapping_status") or ""),
                    "kb_document_id": str(exception.get("kb_document_id") or ""),
                    "maintenance_pack": str(exception.get("maintenance_pack") or ""),
                    "hot_fix_release_label": str(exception.get("hot_fix_release_label") or ""),
                    "about_window_file": str(exception.get("about_window_file") or ""),
                    "bug_patch_number": str(exception.get("bug_patch_number") or ""),
                    "product": str(exception.get("product") or ""),
                    "category": str(exception.get("category") or ""),
                    "description": str(exception.get("description") or ""),
                    "source_html": str(exception.get("source_html") or ""),
                    "evidence_attachment_count": str(exception.get("evidence_attachment_count") or 0),
                    "placeholder_attachment_count": str(exception.get("placeholder_attachment_count") or 0),
                    "evidence_attachment_paths": flatten_list(exception.get("evidence_attachment_paths")),
                    "placeholder_attachment_paths": flatten_list(exception.get("placeholder_attachment_paths")),
                    "mapping_warnings": flatten_list(exception.get("mapping_warnings")),
                    "kb_extraction_warnings": flatten_list(exception.get("kb_extraction_warnings")),
                }
            )
    return rows


def write_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description="Export KB evidence exceptions to a reviewer-friendly CSV."
    )
    parser.add_argument(
        "--exceptions",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_evidence_exceptions.json",
        help="Path to kb_evidence_exceptions.json.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_evidence_exceptions.csv",
        help="CSV output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = read_json(args.exceptions)
    rows = iter_exception_rows(summary)
    write_csv(rows, args.output)

    print(f"Wrote KB evidence exception CSV: {args.output}")
    print(f"Rows exported: {len(rows)}")


if __name__ == "__main__":
    main()
