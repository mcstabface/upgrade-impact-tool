from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Protocol

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.production_semantic_retrieval_enablement_gate import (
    DEFAULT_ENABLEMENT_REPORT,
    build_enablement_gate_report,
    write_enablement_gate_report,
)


DEFAULT_RUNTIME_BOUNDARY_REPORT = "kbs/retrieval/kb_retrieval_runtime_adapter_boundary.v1.json"


@dataclass(frozen=True)
class RetrievalRuntimeRequest:
    requested_adapter: str = "bm25_authoritative"


@dataclass(frozen=True)
class RetrievalRuntimeSelection:
    status: str
    requested_adapter: str
    selected_adapter: str
    reason: str
    bm25_authoritative: bool
    semantic_retrieval_enabled: bool
    hybrid_merge_enabled: bool
    fail_closed: bool
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RetrievalRuntimeBoundaryReport:
    report_version: str
    status: str
    source_enablement_report: str
    live_adapter: str
    supported_adapters: list[str]
    disabled_adapters: list[str]
    selection: RetrievalRuntimeSelection
    semantic_retrieval_enabled: bool
    hybrid_merge_enabled: bool
    bm25_authoritative: bool
    fail_closed: bool


class RetrievalRuntimeAdapter(Protocol):
    adapter_name: str

    def select(self, request: RetrievalRuntimeRequest) -> RetrievalRuntimeSelection:
        """Select a retrieval runtime adapter."""


def read_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def ensure_enablement_report(path: Path) -> None:
    if path.exists():
        return
    root = repo_root()
    citation_preservation = root / "kbs" / "retrieval" / "kb_hybrid_retrieval_citation_preservation.v1.json"
    report = build_enablement_gate_report(citation_preservation_path=citation_preservation)
    write_enablement_gate_report(path, report)


def validate_enablement_report(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"enablement report not found: {path}"]
    report = read_json(path)
    if report.get("status") != "PRODUCTION_SEMANTIC_RETRIEVAL_DISABLED":
        errors.append(f"enablement status must be disabled: {report.get('status')}")
    if report.get("production_semantic_retrieval_enabled") is not False:
        errors.append("production_semantic_retrieval_enabled must be false")
    if report.get("hybrid_merge_enabled") is not False:
        errors.append("hybrid_merge_enabled must be false")
    if report.get("vector_retrieval_authoritative") is not False:
        errors.append("vector_retrieval_authoritative must be false")
    if report.get("bm25_authoritative") is not True:
        errors.append("bm25_authoritative must be true")
    if report.get("fail_closed") is not True:
        errors.append("enablement report must fail closed")
    return errors


class RetrievalRuntimeBoundaryAdapter:
    adapter_name = "runtime_boundary"
    supported_adapters = ["bm25_authoritative"]
    disabled_adapters = ["semantic_vector", "hybrid_retrieval"]

    def __init__(self, enablement_report_path: Path):
        self.enablement_report_path = enablement_report_path

    def select(self, request: RetrievalRuntimeRequest) -> RetrievalRuntimeSelection:
        errors = validate_enablement_report(self.enablement_report_path)
        if errors:
            return RetrievalRuntimeSelection(
                status="REFUSED",
                requested_adapter=request.requested_adapter,
                selected_adapter="none",
                reason="ENABLEMENT_REPORT_INVALID",
                bm25_authoritative=True,
                semantic_retrieval_enabled=False,
                hybrid_merge_enabled=False,
                fail_closed=True,
                errors=errors,
            )
        if request.requested_adapter in self.disabled_adapters:
            return RetrievalRuntimeSelection(
                status="REFUSED",
                requested_adapter=request.requested_adapter,
                selected_adapter="bm25_authoritative",
                reason="REQUESTED_ADAPTER_DISABLED",
                bm25_authoritative=True,
                semantic_retrieval_enabled=False,
                hybrid_merge_enabled=False,
                fail_closed=True,
                errors=[],
            )
        if request.requested_adapter not in self.supported_adapters:
            return RetrievalRuntimeSelection(
                status="REFUSED",
                requested_adapter=request.requested_adapter,
                selected_adapter="none",
                reason="UNSUPPORTED_ADAPTER",
                bm25_authoritative=True,
                semantic_retrieval_enabled=False,
                hybrid_merge_enabled=False,
                fail_closed=True,
                errors=[f"unsupported adapter: {request.requested_adapter}"],
            )
        return RetrievalRuntimeSelection(
            status="SELECTED",
            requested_adapter=request.requested_adapter,
            selected_adapter="bm25_authoritative",
            reason="BM25_AUTHORITATIVE_DEFAULT",
            bm25_authoritative=True,
            semantic_retrieval_enabled=False,
            hybrid_merge_enabled=False,
            fail_closed=True,
            errors=[],
        )


def build_runtime_boundary_report(*, enablement_report_path: Path, requested_adapter: str) -> RetrievalRuntimeBoundaryReport:
    ensure_enablement_report(enablement_report_path)
    adapter = RetrievalRuntimeBoundaryAdapter(enablement_report_path)
    selection = adapter.select(RetrievalRuntimeRequest(requested_adapter=requested_adapter))
    root = repo_root()
    return RetrievalRuntimeBoundaryReport(
        report_version="1",
        status="RETRIEVAL_RUNTIME_BOUNDARY_READY" if selection.status == "SELECTED" else "RETRIEVAL_RUNTIME_BOUNDARY_REFUSED",
        source_enablement_report=str(enablement_report_path.relative_to(root)) if enablement_report_path.is_relative_to(root) else str(enablement_report_path),
        live_adapter="bm25_authoritative",
        supported_adapters=adapter.supported_adapters,
        disabled_adapters=adapter.disabled_adapters,
        selection=selection,
        semantic_retrieval_enabled=False,
        hybrid_merge_enabled=False,
        bm25_authoritative=True,
        fail_closed=True,
    )


def write_runtime_boundary_report(path: Path, report: RetrievalRuntimeBoundaryReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Build retrieval runtime adapter boundary report.")
    parser.add_argument("--enablement-report", type=Path, default=root / DEFAULT_ENABLEMENT_REPORT)
    parser.add_argument("--requested-adapter", default="bm25_authoritative")
    parser.add_argument("--output", type=Path, default=root / DEFAULT_RUNTIME_BOUNDARY_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_runtime_boundary_report(enablement_report_path=args.enablement_report, requested_adapter=args.requested_adapter)
    write_runtime_boundary_report(args.output, report)
    print(f"[gate20a:runtime-boundary] Wrote runtime boundary report: {args.output}")
    print(f"[gate20a:runtime-boundary] status={report.status}")
    print(f"[gate20a:runtime-boundary] live_adapter={report.live_adapter}")
    print(f"[gate20a:runtime-boundary] selected_adapter={report.selection.selected_adapter}")
    print("[gate20a:runtime-boundary] semantic_retrieval_enabled=false")
    print("[gate20a:runtime-boundary] hybrid_merge_enabled=false")


if __name__ == "__main__":
    main()
