from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from app.scripts.extract_kb_source_manifest import build_manifest, repo_root, write_manifest


DEFAULT_RAW_CORPUS_ROOT = "kbs/raw"
DEFAULT_ACTUAL_CORPUS_SOURCE_INVENTORY = "kbs/manifests/actual_corpus_source_inventory.json"
DEFAULT_ACTUAL_CORPUS_SOURCE_INVENTORY_REPORT = "kbs/retrieval/kb_actual_corpus_source_inventory_extraction.v1.json"


@dataclass(frozen=True)
class ActualCorpusSourceInventoryExtractionReport:
    report_version: str
    status: str
    source_root: str
    inventory_manifest_path: str
    source_root_exists: bool
    html_source_count: int
    portfolio_file_count: int
    kb_document_count: int
    missing_portfolio_count: int
    unreferenced_portfolio_count: int
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _relative(path: Path) -> str:
    root = repo_root()
    return str(path.relative_to(root)) if path.is_relative_to(root) else str(path)


def extract_actual_corpus_source_inventory(*, source_root: Path, inventory_output: Path) -> ActualCorpusSourceInventoryExtractionReport:
    errors: list[str] = []
    if not source_root.exists():
        errors.append(f"source root not found: {source_root}")
        return ActualCorpusSourceInventoryExtractionReport(
            report_version="1",
            status="ACTUAL_CORPUS_SOURCE_INVENTORY_EXTRACTION_FAILED",
            source_root=_relative(source_root),
            inventory_manifest_path=_relative(inventory_output),
            source_root_exists=False,
            html_source_count=0,
            portfolio_file_count=0,
            kb_document_count=0,
            missing_portfolio_count=0,
            unreferenced_portfolio_count=0,
            errors=errors,
        )

    manifest = build_manifest(source_root=source_root, output_path=inventory_output)
    write_manifest(manifest, inventory_output)

    missing_count = len(manifest.missing_portfolios)
    unreferenced_count = len(manifest.unreferenced_portfolios)
    kb_document_count = len(manifest.kb_documents)
    warnings = list(manifest.warnings)

    if manifest.html_source_count == 0:
        errors.append("No KB HTML sources were extracted.")
    if manifest.portfolio_file_count == 0:
        errors.append("No PDF portfolio files were extracted.")
    if missing_count:
        warnings.append("One or more referenced portfolio files are missing.")
    if unreferenced_count:
        warnings.append("One or more portfolio files are unreferenced by detected KB HTML sources.")

    status = (
        "ACTUAL_CORPUS_SOURCE_INVENTORY_EXTRACTED"
        if not errors
        else "ACTUAL_CORPUS_SOURCE_INVENTORY_EXTRACTION_FAILED"
    )

    return ActualCorpusSourceInventoryExtractionReport(
        report_version="1",
        status=status,
        source_root=_relative(source_root),
        inventory_manifest_path=_relative(inventory_output),
        source_root_exists=True,
        html_source_count=manifest.html_source_count,
        portfolio_file_count=manifest.portfolio_file_count,
        kb_document_count=kb_document_count,
        missing_portfolio_count=missing_count,
        unreferenced_portfolio_count=unreferenced_count,
        warnings=warnings,
        errors=errors,
    )


def write_extraction_report(path: Path, report: ActualCorpusSourceInventoryExtractionReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Extract source inventory for the actual corpus under kbs/raw.")
    parser.add_argument("--source-root", type=Path, default=root / DEFAULT_RAW_CORPUS_ROOT)
    parser.add_argument("--inventory-output", type=Path, default=root / DEFAULT_ACTUAL_CORPUS_SOURCE_INVENTORY)
    parser.add_argument("--report-output", type=Path, default=root / DEFAULT_ACTUAL_CORPUS_SOURCE_INVENTORY_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = extract_actual_corpus_source_inventory(
        source_root=args.source_root,
        inventory_output=args.inventory_output,
    )
    write_extraction_report(args.report_output, report)
    print(f"[gate21e:source-inventory] Wrote inventory manifest: {args.inventory_output}")
    print(f"[gate21e:source-inventory] Wrote extraction report: {args.report_output}")
    print(f"[gate21e:source-inventory] status={report.status}")
    print(f"[gate21e:source-inventory] source_root={report.source_root}")
    print(f"[gate21e:source-inventory] source_root_exists={'true' if report.source_root_exists else 'false'}")
    print(f"[gate21e:source-inventory] html_source_count={report.html_source_count}")
    print(f"[gate21e:source-inventory] portfolio_file_count={report.portfolio_file_count}")
    print(f"[gate21e:source-inventory] kb_document_count={report.kb_document_count}")
    print(f"[gate21e:source-inventory] missing_portfolio_count={report.missing_portfolio_count}")
    print(f"[gate21e:source-inventory] unreferenced_portfolio_count={report.unreferenced_portfolio_count}")


if __name__ == "__main__":
    main()
