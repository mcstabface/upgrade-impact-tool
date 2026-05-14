from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_RAW_CORPUS_ROOT = "kbs/raw"
DEFAULT_DEMO_READINESS_REPORT = "kbs/retrieval/kb_actual_corpus_demo_readiness.v1.json"


@dataclass(frozen=True)
class CorpusSampleFile:
    path: str
    suffix: str
    size_bytes: int


@dataclass(frozen=True)
class ActualCorpusDemoReadinessReport:
    report_version: str
    status: str
    corpus_root: str
    corpus_root_exists: bool
    file_count: int
    total_size_bytes: int
    extension_counts: dict[str, int]
    sample_files: list[CorpusSampleFile]
    demo_readiness_checks: dict[str, str]
    recommended_next_steps: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _relative(path: Path) -> str:
    root = repo_root()
    return str(path.relative_to(root)) if path.is_relative_to(root) else str(path)


def _iter_files(corpus_root: Path) -> list[Path]:
    return sorted(path for path in corpus_root.rglob("*") if path.is_file())


def _suffix(path: Path) -> str:
    suffix = path.suffix.lower().strip()
    return suffix if suffix else "[no_extension]"


def build_actual_corpus_demo_readiness_report(*, corpus_root: Path, sample_limit: int = 25) -> ActualCorpusDemoReadinessReport:
    errors: list[str] = []
    recommended_next_steps: list[str] = []

    if not corpus_root.exists():
        errors.append(f"corpus root not found: {corpus_root}")
        return ActualCorpusDemoReadinessReport(
            report_version="1",
            status="ACTUAL_CORPUS_NOT_READY",
            corpus_root=_relative(corpus_root),
            corpus_root_exists=False,
            file_count=0,
            total_size_bytes=0,
            extension_counts={},
            sample_files=[],
            demo_readiness_checks={
                "corpus_root_exists": "FAIL",
                "has_files": "FAIL",
                "has_sample_files": "FAIL",
            },
            recommended_next_steps=["Confirm the actual corpus exists under kbs/raw before demo preparation."],
            errors=errors,
        )

    files = _iter_files(corpus_root)
    extension_counts = Counter(_suffix(path) for path in files)
    total_size_bytes = sum(path.stat().st_size for path in files)
    sample_files = [
        CorpusSampleFile(path=_relative(path), suffix=_suffix(path), size_bytes=path.stat().st_size)
        for path in files[:sample_limit]
    ]

    checks = {
        "corpus_root_exists": "PASS",
        "has_files": "PASS" if files else "FAIL",
        "has_sample_files": "PASS" if sample_files else "FAIL",
    }

    if not files:
        errors.append(f"corpus root contains no files: {corpus_root}")
        recommended_next_steps.append("Populate kbs/raw with the actual corpus before demo preparation.")
    else:
        recommended_next_steps.extend(
            [
                "Run ingestion over kbs/raw or confirm existing ingestion artifacts for this corpus.",
                "Collect 5-10 customer-relevant demo questions against this corpus.",
                "Run retrieval against the ingested artifacts and record evidence quality before customer review.",
            ]
        )

    status = "ACTUAL_CORPUS_READY_FOR_INGESTION_ASSESSMENT" if not errors else "ACTUAL_CORPUS_NOT_READY"
    return ActualCorpusDemoReadinessReport(
        report_version="1",
        status=status,
        corpus_root=_relative(corpus_root),
        corpus_root_exists=True,
        file_count=len(files),
        total_size_bytes=total_size_bytes,
        extension_counts=dict(sorted(extension_counts.items())),
        sample_files=sample_files,
        demo_readiness_checks=checks,
        recommended_next_steps=recommended_next_steps,
        errors=errors,
    )


def write_demo_readiness_report(path: Path, report: ActualCorpusDemoReadinessReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Report actual corpus demo readiness.")
    parser.add_argument("--corpus-root", type=Path, default=root / DEFAULT_RAW_CORPUS_ROOT)
    parser.add_argument("--sample-limit", type=int, default=25)
    parser.add_argument("--output", type=Path, default=root / DEFAULT_DEMO_READINESS_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_actual_corpus_demo_readiness_report(corpus_root=args.corpus_root, sample_limit=args.sample_limit)
    write_demo_readiness_report(args.output, report)
    print(f"[gate21c:actual-corpus] Wrote demo readiness report: {args.output}")
    print(f"[gate21c:actual-corpus] status={report.status}")
    print(f"[gate21c:actual-corpus] corpus_root={report.corpus_root}")
    print(f"[gate21c:actual-corpus] corpus_root_exists={'true' if report.corpus_root_exists else 'false'}")
    print(f"[gate21c:actual-corpus] file_count={report.file_count}")
    print(f"[gate21c:actual-corpus] total_size_bytes={report.total_size_bytes}")
    print(f"[gate21c:actual-corpus] extension_count={len(report.extension_counts)}")


if __name__ == "__main__":
    main()
