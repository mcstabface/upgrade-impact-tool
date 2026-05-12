from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import relpath, repo_root

STATUS_COUNT_RE = re.compile(r"^- (?P<label>.*?): (?P<count>\d+)\s*$")
HIGH_EXCEPTION_ROW_RE = re.compile(r"^\| (?P<kb>KB\d+) \| (?P<mp>.*?) \| (?P<release_date>.*?) \| (?P<bug_patch_number>.*?) \| (?P<product>.*?) \| (?P<category>.*?) \| (?P<portfolio>.*?) \| (?P<description>.*?) \|$")


@dataclass(frozen=True)
class Gate7EnrichedImpactContext:
    artifact_type: str
    schema_version: str
    generated_utc: str
    source_context_path: str
    source_context_schema_version: str
    assembly_status: str
    generation_policy: dict[str, Any]
    source_inputs: dict[str, Any]
    target_context: dict[str, Any]
    diagnostics: dict[str, Any]
    warnings: list[str]
    evidence_exception_context: dict[str, Any]
    evidence_groups: list[dict[str, Any]]
    evidence_items: list[dict[str, Any]]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return path.read_text(encoding="utf-8")


def search_manifest_by_child_sha(search_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    by_sha: dict[str, dict[str, Any]] = {}
    for artifact in search_manifest.get("artifacts", []):
        child_sha = artifact.get("child_sha256")
        if child_sha:
            by_sha[child_sha] = artifact
    return by_sha


def parse_exception_summary(summary_text: str, *, source_path: Path) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    severity_counts: dict[str, int] = {}
    high_severity: list[dict[str, Any]] = []
    current_section = ""

    for raw_line in summary_text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            current_section = line.removeprefix("## ").strip()
            continue
        if current_section in {"Status Counts", "Severity Counts"}:
            match = STATUS_COUNT_RE.match(line)
            if match:
                target = status_counts if current_section == "Status Counts" else severity_counts
                target[match.group("label")] = int(match.group("count"))
        if current_section == "High-Severity Exceptions":
            match = HIGH_EXCEPTION_ROW_RE.match(line)
            if match and match.group("kb") != "KB":
                high_severity.append(
                    {
                        "kb_document_id": match.group("kb"),
                        "maintenance_pack": match.group("mp"),
                        "release_date": match.group("release_date"),
                        "bug_patch_number": match.group("bug_patch_number"),
                        "product": match.group("product"),
                        "category": match.group("category"),
                        "portfolio_file": match.group("portfolio"),
                        "description": match.group("description"),
                        "severity": "High",
                        "status": "Missing extracted PFDS evidence",
                    }
                )

    return {
        "source_path": relpath(source_path, repo_root()),
        "status_counts": status_counts,
        "severity_counts": severity_counts,
        "high_severity_exceptions": high_severity,
        "high_severity_count": len(high_severity),
    }


def enrichment_for_item(item: dict[str, Any], search_by_sha: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], list[str]]:
    child_sha = item.get("child_sha256")
    artifact = search_by_sha.get(child_sha or "")
    warnings: list[str] = []
    enriched = dict(item)

    if not artifact:
        warnings.append(f"No search-context manifest artifact found for evidence_id={item.get('evidence_id')} child_sha256={child_sha}")
        enriched["pdf_context_flags"] = {
            "status": "MISSING_SEARCH_CONTEXT_MANIFEST_ROW",
            "has_images": None,
            "image_count": None,
            "has_highlight_annotations": None,
            "highlight_annotation_count": None,
            "text_extraction_status": "UNKNOWN",
        }
        return enriched, warnings

    enriched["pdf_context_flags"] = {
        "status": "FOUND",
        "artifact_path": artifact.get("artifact_path"),
        "has_images": artifact.get("has_images"),
        "image_count": artifact.get("image_count"),
        "has_highlight_annotations": artifact.get("has_highlight_annotations"),
        "highlight_annotation_count": artifact.get("highlight_annotation_count"),
        "text_extraction_status": "HAS_TEXT" if int(artifact.get("char_count") or 0) > 0 else "EMPTY_TEXT",
        "page_count": artifact.get("page_count"),
        "char_count": artifact.get("char_count"),
    }
    return enriched, warnings


def build_enriched_context(
    *,
    source_context_path: Path,
    search_context_manifest_path: Path,
    exception_summary_path: Path,
    output_path: Path,
) -> Gate7EnrichedImpactContext:
    root = repo_root()
    source_context = read_json(source_context_path)
    search_manifest = read_json(search_context_manifest_path)
    exception_context = parse_exception_summary(read_text(exception_summary_path), source_path=exception_summary_path)
    search_by_sha = search_manifest_by_child_sha(search_manifest)

    warnings = list(source_context.get("warnings") or [])
    enriched_items: list[dict[str, Any]] = []
    image_bearing_count = 0
    missing_pdf_flag_count = 0

    for item in source_context.get("evidence_items", []):
        enriched_item, item_warnings = enrichment_for_item(item, search_by_sha)
        warnings.extend(item_warnings)
        flags = enriched_item.get("pdf_context_flags") or {}
        if flags.get("has_images") is True:
            image_bearing_count += 1
        if flags.get("status") != "FOUND":
            missing_pdf_flag_count += 1
        enriched_items.append(enriched_item)

    source_inputs = dict(source_context.get("source_inputs") or {})
    source_inputs.update(
        {
            "source_context_path": relpath(source_context_path, root),
            "search_context_manifest_path": relpath(search_context_manifest_path, root),
            "exception_summary_path": relpath(exception_summary_path, root),
            "output_path": relpath(output_path, root),
        }
    )

    diagnostics = dict(source_context.get("diagnostics") or {})
    diagnostics.update(
        {
            "pdf_context_flags_enriched_items": len(enriched_items) - missing_pdf_flag_count,
            "missing_pdf_context_flag_count": missing_pdf_flag_count,
            "image_bearing_evidence_items": image_bearing_count,
            "high_severity_evidence_exceptions": exception_context.get("high_severity_count", 0),
        }
    )

    return Gate7EnrichedImpactContext(
        artifact_type="kb_impact_context",
        schema_version="kb_impact_context.v2",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        source_context_path=relpath(source_context_path, root),
        source_context_schema_version=source_context.get("schema_version", "UNKNOWN"),
        assembly_status="ENRICHED_EVIDENCE_ONLY_NO_GENERATED_CLAIMS",
        generation_policy=source_context.get("generation_policy", {}),
        source_inputs=source_inputs,
        target_context=source_context.get("target_context", {}),
        diagnostics=diagnostics,
        warnings=warnings,
        evidence_exception_context=exception_context,
        evidence_groups=source_context.get("evidence_groups", []),
        evidence_items=enriched_items,
    )


def write_context(context: Gate7EnrichedImpactContext, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(context), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Enrich Gate 6 impact context with PFDS flags and Gate 1 exception context.")
    parser.add_argument("--source-context", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_context.v1.json")
    parser.add_argument("--search-context-manifest", type=Path, default=root / "kbs" / "manifests" / "kb_search_context_manifest.json")
    parser.add_argument("--exception-summary", type=Path, default=root / "kbs" / "manifests" / "kb_evidence_exception_summary.md")
    parser.add_argument("--output", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_context.v2.enriched.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    context = build_enriched_context(
        source_context_path=args.source_context,
        search_context_manifest_path=args.search_context_manifest,
        exception_summary_path=args.exception_summary,
        output_path=args.output,
    )
    write_context(context, args.output)
    print(f"Wrote enriched KB impact context: {args.output}")
    print(f"Evidence items: {len(context.evidence_items)}")
    print(f"Image-bearing evidence items: {context.diagnostics['image_bearing_evidence_items']}")
    print(f"High-severity evidence exceptions: {context.diagnostics['high_severity_evidence_exceptions']}")
    print(f"Warnings: {len(context.warnings)}")


if __name__ == "__main__":
    main()
