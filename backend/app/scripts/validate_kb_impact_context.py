from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


@dataclass(frozen=True)
class ValidationFailure:
    check: str
    detail: str


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_generation_policy(context: dict[str, Any]) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    if context.get("artifact_type") != "kb_impact_context":
        failures.append(
            ValidationFailure(
                check="artifact_type",
                detail=f"Expected kb_impact_context; found {context.get('artifact_type')!r}.",
            )
        )
    if context.get("schema_version") != "kb_impact_context.v1":
        failures.append(
            ValidationFailure(
                check="schema_version",
                detail=f"Expected kb_impact_context.v1; found {context.get('schema_version')!r}.",
            )
        )
    if context.get("assembly_status") != "EVIDENCE_ONLY_NO_GENERATED_CLAIMS":
        failures.append(
            ValidationFailure(
                check="assembly_status",
                detail=f"Unexpected assembly status: {context.get('assembly_status')!r}.",
            )
        )

    policy = context.get("generation_policy")
    if not isinstance(policy, dict):
        return [ValidationFailure(check="generation_policy", detail="Expected generation_policy object.")]

    for field in ["llm_used", "impact_claims_generated", "summaries_generated"]:
        if policy.get(field) is not False:
            failures.append(
                ValidationFailure(
                    check=f"generation_policy.{field}",
                    detail=f"Expected False; found {policy.get(field)!r}.",
                )
            )
    return failures


def validate_evidence_items(context: dict[str, Any]) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    items = context.get("evidence_items")
    if not isinstance(items, list) or not items:
        return [ValidationFailure(check="evidence_items", detail="Expected non-empty evidence_items list.")]

    required_fields = {
        "evidence_id",
        "case_id",
        "query",
        "ranker",
        "rank",
        "score",
        "chunk_id",
        "matched_terms",
        "kb_document_id",
        "bug_patch_number",
        "product",
        "category",
        "child_pdf_path",
        "child_sha256",
        "text_sha256",
        "text",
    }

    seen_ids: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            failures.append(ValidationFailure(check=f"evidence_items[{index}]", detail="Expected evidence item object."))
            continue
        missing = sorted(required_fields - set(item))
        if missing:
            failures.append(
                ValidationFailure(
                    check=f"evidence_items[{index}].required_fields",
                    detail=f"Missing required fields: {', '.join(missing)}.",
                )
            )
        evidence_id = item.get("evidence_id")
        if evidence_id in seen_ids:
            failures.append(
                ValidationFailure(
                    check=f"evidence_items[{index}].evidence_id",
                    detail=f"Duplicate evidence_id: {evidence_id}.",
                )
            )
        seen_ids.add(str(evidence_id))
        if not item.get("text"):
            failures.append(ValidationFailure(check=f"evidence_items[{index}].text", detail="Evidence item text is empty."))
        if not item.get("chunk_id"):
            failures.append(ValidationFailure(check=f"evidence_items[{index}].chunk_id", detail="chunk_id is empty."))
        if not item.get("child_pdf_path"):
            failures.append(ValidationFailure(check=f"evidence_items[{index}].child_pdf_path", detail="child_pdf_path is empty."))
    return failures


def validate_evidence_groups(context: dict[str, Any]) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    groups = context.get("evidence_groups")
    items = context.get("evidence_items") or []
    item_ids = {item.get("evidence_id") for item in items if isinstance(item, dict)}
    if not isinstance(groups, list) or not groups:
        return [ValidationFailure(check="evidence_groups", detail="Expected non-empty evidence_groups list.")]

    for index, group in enumerate(groups):
        if not isinstance(group, dict):
            failures.append(ValidationFailure(check=f"evidence_groups[{index}]", detail="Expected evidence group object."))
            continue
        for field in ["group_key", "kb_document_id", "bug_patch_number", "product", "category", "evidence_count", "evidence_ids"]:
            if field not in group:
                failures.append(
                    ValidationFailure(check=f"evidence_groups[{index}].{field}", detail="Missing required group field.")
                )
        evidence_ids = group.get("evidence_ids") or []
        if len(evidence_ids) != group.get("evidence_count"):
            failures.append(
                ValidationFailure(
                    check=f"evidence_groups[{index}].evidence_count",
                    detail="evidence_count does not match evidence_ids length.",
                )
            )
        missing_ids = sorted(evidence_id for evidence_id in evidence_ids if evidence_id not in item_ids)
        if missing_ids:
            failures.append(
                ValidationFailure(
                    check=f"evidence_groups[{index}].evidence_ids",
                    detail=f"Group references missing evidence item IDs: {', '.join(missing_ids)}.",
                )
            )
    return failures


def validate(context_path: Path) -> list[ValidationFailure]:
    context = read_json(context_path)
    failures: list[ValidationFailure] = []
    failures.extend(validate_generation_policy(context))
    failures.extend(validate_evidence_items(context))
    failures.extend(validate_evidence_groups(context))

    diagnostics = context.get("diagnostics")
    if not isinstance(diagnostics, dict):
        failures.append(ValidationFailure(check="diagnostics", detail="Expected diagnostics object."))
    else:
        if int(diagnostics.get("assembled_evidence_items") or 0) <= 0:
            failures.append(
                ValidationFailure(check="diagnostics.assembled_evidence_items", detail="Expected assembled evidence items > 0.")
            )
        if int(diagnostics.get("evidence_groups") or 0) <= 0:
            failures.append(ValidationFailure(check="diagnostics.evidence_groups", detail="Expected evidence groups > 0."))

    return failures


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 6 KB impact context artifact.")
    parser.add_argument(
        "--context",
        type=Path,
        default=root / "kbs" / "impact_context" / "kb_impact_context.v1.json",
        help="Impact context artifact path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures = validate(args.context)
    if failures:
        print("[gate6:validate] FAILED")
        for failure in failures:
            print(f"[gate6:validate] {failure.check}: {failure.detail}")
        raise SystemExit(1)

    print("[gate6:validate] OK")
    print(f"[gate6:validate] context={args.context}")


if __name__ == "__main__":
    main()
