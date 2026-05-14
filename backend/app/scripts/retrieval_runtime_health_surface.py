from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.retrieval_runtime_adapter_boundary import (
    DEFAULT_RUNTIME_BOUNDARY_REPORT,
    build_runtime_boundary_report,
    read_json,
    write_runtime_boundary_report,
)


DEFAULT_RUNTIME_HEALTH_REPORT = "kbs/retrieval/kb_retrieval_runtime_health_surface.v1.json"


@dataclass(frozen=True)
class RetrievalRuntimeHealthCheck:
    name: str
    status: str
    observed: str
    expected: str


@dataclass(frozen=True)
class RetrievalRuntimeHealthSurfaceReport:
    report_version: str
    status: str
    source_boundary_report: str
    live_adapter: str
    bm25_authoritative: bool
    semantic_retrieval_enabled: bool
    hybrid_merge_enabled: bool
    fail_closed: bool
    health_checks: list[RetrievalRuntimeHealthCheck]
    errors: list[str] = field(default_factory=list)


def ensure_boundary_report(path: Path, *, enablement_report_path: Path, requested_adapter: str) -> None:
    if path.exists():
        return
    report = build_runtime_boundary_report(
        enablement_report_path=enablement_report_path,
        requested_adapter=requested_adapter,
    )
    write_runtime_boundary_report(path, report)


def _bool_text(value: object) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def _check_bool(name: str, observed: object, expected: bool) -> RetrievalRuntimeHealthCheck:
    return RetrievalRuntimeHealthCheck(
        name=name,
        status="PASS" if observed is expected else "FAIL",
        observed=_bool_text(observed),
        expected=_bool_text(expected),
    )


def _check_text(name: str, observed: object, expected: str) -> RetrievalRuntimeHealthCheck:
    observed_text = str(observed)
    return RetrievalRuntimeHealthCheck(
        name=name,
        status="PASS" if observed_text == expected else "FAIL",
        observed=observed_text,
        expected=expected,
    )


def build_runtime_health_surface_report(*, boundary_report_path: Path) -> RetrievalRuntimeHealthSurfaceReport:
    root = repo_root()
    boundary_report = read_json(boundary_report_path)
    selection = boundary_report.get("selection")
    if not isinstance(selection, dict):
        selection = {}

    checks = [
        _check_text("boundary_status", boundary_report.get("status"), "RETRIEVAL_RUNTIME_BOUNDARY_READY"),
        _check_text("live_adapter", boundary_report.get("live_adapter"), "bm25_authoritative"),
        _check_text("selected_adapter", selection.get("selected_adapter"), "bm25_authoritative"),
        _check_bool("bm25_authoritative", boundary_report.get("bm25_authoritative"), True),
        _check_bool("semantic_retrieval_enabled", boundary_report.get("semantic_retrieval_enabled"), False),
        _check_bool("hybrid_merge_enabled", boundary_report.get("hybrid_merge_enabled"), False),
        _check_bool("fail_closed", boundary_report.get("fail_closed"), True),
    ]

    errors = [
        f"{check.name}: observed={check.observed} expected={check.expected}"
        for check in checks
        if check.status != "PASS"
    ]
    status = "RETRIEVAL_RUNTIME_HEALTHY" if not errors else "RETRIEVAL_RUNTIME_UNHEALTHY"

    return RetrievalRuntimeHealthSurfaceReport(
        report_version="1",
        status=status,
        source_boundary_report=str(boundary_report_path.relative_to(root)) if boundary_report_path.is_relative_to(root) else str(boundary_report_path),
        live_adapter=str(boundary_report.get("live_adapter")),
        bm25_authoritative=boundary_report.get("bm25_authoritative") is True,
        semantic_retrieval_enabled=boundary_report.get("semantic_retrieval_enabled") is True,
        hybrid_merge_enabled=boundary_report.get("hybrid_merge_enabled") is True,
        fail_closed=boundary_report.get("fail_closed") is True,
        health_checks=checks,
        errors=errors,
    )


def write_runtime_health_surface_report(path: Path, report: RetrievalRuntimeHealthSurfaceReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Build retrieval runtime health surface report.")
    parser.add_argument("--boundary-report", type=Path, default=root / DEFAULT_RUNTIME_BOUNDARY_REPORT)
    parser.add_argument("--enablement-report", type=Path, default=root / "kbs/retrieval/kb_production_semantic_retrieval_enablement_gate.v1.json")
    parser.add_argument("--requested-adapter", default="bm25_authoritative")
    parser.add_argument("--output", type=Path, default=root / DEFAULT_RUNTIME_HEALTH_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_boundary_report(
        args.boundary_report,
        enablement_report_path=args.enablement_report,
        requested_adapter=args.requested_adapter,
    )
    report = build_runtime_health_surface_report(boundary_report_path=args.boundary_report)
    write_runtime_health_surface_report(args.output, report)
    print(f"[gate20b:runtime-health] Wrote runtime health report: {args.output}")
    print(f"[gate20b:runtime-health] status={report.status}")
    print(f"[gate20b:runtime-health] live_adapter={report.live_adapter}")
    print(f"[gate20b:runtime-health] bm25_authoritative={_bool_text(report.bm25_authoritative)}")
    print(f"[gate20b:runtime-health] semantic_retrieval_enabled={_bool_text(report.semantic_retrieval_enabled)}")
    print(f"[gate20b:runtime-health] hybrid_merge_enabled={_bool_text(report.hybrid_merge_enabled)}")
    print(f"[gate20b:runtime-health] fail_closed={_bool_text(report.fail_closed)}")


if __name__ == "__main__":
    main()
