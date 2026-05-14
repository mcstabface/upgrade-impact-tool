from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from app.scripts.extract_kb_source_manifest import build_manifest, repo_root


DEFAULT_RAW_CORPUS_ROOT = "kbs/raw"
DEFAULT_INGESTION_DRY_RUN_REPORT = "kbs/retrieval/kb_actual_corpus_ingestion_dry_run.v1.json"


@dataclass(frozen=True)
class ActualCorpusIngestionDryRunReport:
    report_version: str
    status: str
    source_root: str
    source_root_exists: bool
    html_source_count: int
    portfolio_file_count: int
    missing_portfolio_count: int
    unreferenced_portfolio_count: int
    kb_document_count: int
    dry_run_checks: dict[str, str]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    recommended_next_steps: list[str] = field(default_factory=list)


def _relative(path: Path) -> str:
    root = repo_root()
    return str(path.relative_to(root)) if path.is_relative_to(root) else str(path)


def build_actual_corpus_ingestion_dry_run_report(*, source_root: Path) -> ActualCorpusIngestionDryRunReport:
    errors: list[str] = []
    warnings: list[str] = []
    recommended_next_steps: list[str] = []

    if not source_root.exists():
        errors.append(f"source root not found: {source_root}")
        return ActualCorpusIngestionDryRunReport(
            report_version="1",
            status="ACTUAL_CORPUS_INGESTION_DRY_RUN_NOT_READY",
            source_root=_relative(source_root),
            source_root_exists=False,
            html_source_count=0,
            portfolio_file_count=0,
            missing_portfolio_count=0,
            unreferenced_portfolio_count=0,
            kb_document_count=0,
            dry_run_checks={
                "source_root_exists": "FAIL",
                "has_html_sources": "FAIL",
                "has_portfolio_files": "FAIL",
                "manifest_buildable": "FAIL",
            },
            errors=errors,
            recommended_next_steps=["Confirm the actual corpus exists under kbs/raw before ingestion dry run."],
        )

    manifest = build_manifest(source_root=source_root, output_path=repo_root() / DEFAULT_INGESTION_DRY_RUN_REPORT)
    html_count = manifest.html_source_count
    portfolio_count = manifest.portfolio_file_count
    missing_count = len(manifest.missing_portfolios)
    unreferenced_count = len(manifest.unreferenced_portfolios)
    kb_document_count = len(manifest.kb_documents)

    checks = {
        "source_root_exists": "PASS",
        "has_html_sources": "PASS" if html_count > 0 else "FAIL",
        "has_portfolio_files": "PASS" if portfolio_count > 0 else "FAIL",
        "manifest_buildable": "PASS",
        "missing_portfolios_clear": "PASS" if missing_count == 0 else "WARN",
    }

    warnings.extend(manifest.warnings)
    if missing_count:
        warnings.append("One or more referenced portfolio files are missing.")
    if unreferenced_count:
        warnings.append("One or more portfolio files are not referenced by detected KB HTML sources.")

    if html_count == 0:
        errors.append("No KB HTML sources were detected under kbs/raw.")
    if portfolio_count == 0:
        errors.append("No PDF portfolio files were detected under kbs/raw.")

    if errors:
        status = "ACTUAL_CORPUS_INGESTION_DRY_RUN_NOT_READY"
        recommended_next_steps.append("Resolve missing HTML or portfolio sources before ingestion.")
    elif warnings:
        status = "ACTUAL_CORPUS_INGESTION_DRY_RUN_READY_WITH_WARNINGS"
        recommended_next_steps.extend(
            [
                "Review missing or unreferenced portfolio warnings before customer demo.",
                "Run the actual source inventory extraction if warnings are acceptable.",
            ]
        )
    else:
        status = "ACTUAL_CORPUS_INGESTION_DRY_RUN_READY"
        recommended_next_steps.extend(
            [
                "Run the actual source inventory extraction over kbs/raw.",
                "Proceed to search-context extraction after inventory generation.",
            ]
        )

    return ActualCorpusIngestionDryRunReport(
        report_version="1",
        status=status,
        source_root=_relative(source_root),
        source_root_exists=True,
        html_source_count=html_count,
        portfolio_file_count=portfolio_count,
        missing_portfolio_count=missing_count,
        unreferenced_portfolio_count=unreferenced_count,
        kb_document_count=kb_document_count,
        dry_run_checks=checks,
        warnings=warnings,
        errors=errors,
        recommended_next_steps=recommended_next_steps,
    )


def write_ingestion_dry_run_report(path: Path, report: ActualCorpusIngestionDryRunReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Dry-run actual corpus ingestion readiness.")
    parser.add_argument("--source-root", type=Path, default=root / DEFAULT_RAW_CORPUS_ROOT)
    parser.add_argument("--output", type=Path, default=root / DEFAULT_INGESTION_DRY_RUN_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_actual_corpus_ingestion_dry_run_report(source_root=args.source_root)
    write_ingestion_dry_run_report(args.output, report)
    print(f"[gate21d:ingestion-dry-run] Wrote ingestion dry-run report: {args.output}")
    print(f"[gate21d:ingestion-dry-run] status={report.status}")
    print(f"[gate21d:ingestion-dry-run] source_root={report.source_root}")
    print(f"[gate21d:ingestion-dry-run] source_root_exists={'true' if report.source_root_exists else 'false'}")
    print(f"[gate21d:ingestion-dry-run] html_source_count={report.html_source_count}")
    print(f"[gate21d:ingestion-dry-run] portfolio_file_count={report.portfolio_file_count}")
    print(f"[gate21d:ingestion-dry-run] missing_portfolio_count={report.missing_portfolio_count}")
    print(f"[gate21d:ingestion-dry-run] unreferenced_portfolio_count={report.unreferenced_portfolio_count}")
    print(f"[gate21d:ingestion-dry-run] kb_document_count={report.kb_document_count}")


if __name__ == "__main__":
    main()
