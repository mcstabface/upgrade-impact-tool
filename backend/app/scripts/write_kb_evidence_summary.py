from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root

STATUS_LABELS = {
    "NO_EVIDENCE_ATTACHMENT_FOUND": "Missing extracted PFDS evidence",
    "ROW_MISSING_FIX_IDENTIFIER": "KB row missing bug / patch identifier",
    "KB_DECLARED_NO_PFD": "KB explicitly declares no PFD",
    "PORTFOLIO_PLACEHOLDER_NO_PFDS": "Portfolio contains no-PFDS placeholder",
    "MULTIPLE_EVIDENCE_CANDIDATES": "Multiple extracted PFDS candidates",
    "ROW_MISSING_PORTFOLIO_REFERENCE": "KB row missing portfolio reference",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_exception_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for document in summary.get("documents", []):
        rows.extend(document.get("exceptions", []))
    return rows


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key) or "UNKNOWN") for row in rows).items()))


def format_status(status: str) -> str:
    return STATUS_LABELS.get(status, status.replace("_", " ").title())


def write_section_counts(lines: list[str], title: str, counts: dict[str, int]) -> None:
    lines.append(f"## {title}")
    lines.append("")
    if not counts:
        lines.append("None.")
        lines.append("")
        return

    for key, count in counts.items():
        label = format_status(key) if title == "Status Counts" else key.title()
        lines.append(f"- {label}: {count}")
    lines.append("")


def write_high_severity_table(lines: list[str], rows: list[dict[str, Any]]) -> None:
    high_rows = [row for row in rows if row.get("severity") == "HIGH"]
    lines.append("## High-Severity Exceptions")
    lines.append("")
    if not high_rows:
        lines.append("No high-severity exceptions found.")
        lines.append("")
        return

    lines.append("| KB | MP | Release Date | Bug / Patch | Product | Category | Portfolio | Description |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for row in high_rows:
        lines.append(
            "| "
            + " | ".join(
                sanitize_table_cell(str(value or ""))
                for value in [
                    row.get("kb_document_id"),
                    row.get("maintenance_pack"),
                    row.get("hot_fix_release_label"),
                    row.get("bug_patch_number"),
                    row.get("product"),
                    row.get("category"),
                    row.get("about_window_file"),
                    row.get("description"),
                ]
            )
            + " |"
        )
    lines.append("")


def write_document_breakdown(lines: list[str], summary: dict[str, Any]) -> None:
    lines.append("## Document Breakdown")
    lines.append("")
    for document in summary.get("documents", []):
        lines.append(
            f"### {document.get('kb_document_id') or 'Unknown KB'} — "
            f"{document.get('maintenance_pack') or 'Unknown MP'}"
        )
        lines.append("")
        lines.append(f"Source: `{document.get('source_html')}`")
        lines.append("")
        lines.append(f"Exception count: {document.get('exception_count', 0)}")
        lines.append("")
        status_counts = document.get("status_counts", {})
        for status, count in sorted(status_counts.items()):
            lines.append(f"- {format_status(status)}: {count}")
        lines.append("")


def sanitize_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").replace("\r", " ").strip()


def build_report(summary: dict[str, Any]) -> str:
    rows = iter_exception_rows(summary)
    generated = datetime.now(timezone.utc).isoformat()

    lines: list[str] = []
    lines.append("# KB Evidence Exception Summary")
    lines.append("")
    lines.append(f"Generated UTC: `{generated}`")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"- Documents with exceptions: {summary.get('document_count', 0)}")
    lines.append(f"- Total exceptions: {summary.get('exception_count', 0)}")
    lines.append(f"- High-severity exceptions: {summary.get('severity_counts', {}).get('HIGH', 0)}")
    lines.append(f"- Medium-severity exceptions: {summary.get('severity_counts', {}).get('MEDIUM', 0)}")
    lines.append(f"- Low-severity exceptions: {summary.get('severity_counts', {}).get('LOW', 0)}")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "High-severity exceptions are KB rows that reference a bug / patch number but did not map "
        "to an extracted PFDS attachment in the referenced portfolio. These are the primary review candidates."
    )
    lines.append("")
    lines.append(
        "Medium-severity exceptions are KB rows that cannot be joined automatically because the row does "
        "not include a bug / patch identifier or has ambiguous evidence. These need source review before automation can claim coverage."
    )
    lines.append("")
    lines.append(
        "Low-severity exceptions are cases where the KB or portfolio explicitly indicates that no PFD was provided. "
        "These are not missing-evidence failures, but they should remain visible because they affect downstream analysis depth."
    )
    lines.append("")

    write_section_counts(lines, "Severity Counts", summary.get("severity_counts", {}))
    write_section_counts(lines, "Status Counts", summary.get("status_counts", {}))
    write_section_counts(lines, "Exceptions by KB", count_by(rows, "kb_document_id"))
    write_high_severity_table(lines, rows)
    write_document_breakdown(lines, summary)

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description="Write a Markdown summary report for KB evidence exceptions."
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
        default=root / "kbs" / "manifests" / "kb_evidence_exception_summary.md",
        help="Markdown report output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = read_json(args.exceptions)
    report = build_report(summary)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")

    print(f"Wrote KB evidence summary report: {args.output}")
    print(f"Exceptions summarized: {summary.get('exception_count', 0)}")


if __name__ == "__main__":
    main()
