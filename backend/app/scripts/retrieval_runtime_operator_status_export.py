from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.retrieval_runtime_adapter_boundary import DEFAULT_RUNTIME_BOUNDARY_REPORT
from app.scripts.retrieval_runtime_health_surface import (
    DEFAULT_RUNTIME_HEALTH_REPORT,
    build_runtime_health_surface_report,
    ensure_boundary_report,
    write_runtime_health_surface_report,
)


DEFAULT_OPERATOR_STATUS_EXPORT = "kbs/retrieval/kb_retrieval_runtime_operator_status.v1.md"


@dataclass(frozen=True)
class RetrievalRuntimeOperatorStatus:
    title: str
    status: str
    live_adapter: str
    bm25_authoritative: bool
    semantic_retrieval_enabled: bool
    hybrid_merge_enabled: bool
    fail_closed: bool
    operator_summary: str
    action_required: str


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def build_operator_status(*, health_report_path: Path) -> RetrievalRuntimeOperatorStatus:
    report = build_runtime_health_surface_report(boundary_report_path=health_report_path)
    healthy = report.status == "RETRIEVAL_RUNTIME_HEALTHY"
    return RetrievalRuntimeOperatorStatus(
        title="Retrieval Runtime Operator Status",
        status=report.status,
        live_adapter=report.live_adapter,
        bm25_authoritative=report.bm25_authoritative,
        semantic_retrieval_enabled=report.semantic_retrieval_enabled,
        hybrid_merge_enabled=report.hybrid_merge_enabled,
        fail_closed=report.fail_closed,
        operator_summary=(
            "Retrieval runtime is healthy. BM25 is authoritative and semantic retrieval remains disabled."
            if healthy
            else "Retrieval runtime is unhealthy. Review health check failures before operator use."
        ),
        action_required="none" if healthy else "investigate_runtime_health",
    )


def render_operator_status(status: RetrievalRuntimeOperatorStatus) -> str:
    lines = [
        f"# {status.title}",
        "",
        "## Summary",
        "",
        status.operator_summary,
        "",
        "## Runtime State",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| status | `{status.status}` |",
        f"| live_adapter | `{status.live_adapter}` |",
        f"| bm25_authoritative | `{_bool_text(status.bm25_authoritative)}` |",
        f"| semantic_retrieval_enabled | `{_bool_text(status.semantic_retrieval_enabled)}` |",
        f"| hybrid_merge_enabled | `{_bool_text(status.hybrid_merge_enabled)}` |",
        f"| fail_closed | `{_bool_text(status.fail_closed)}` |",
        "",
        "## Operator Action",
        "",
        f"`{status.action_required}`",
        "",
    ]
    return "\n".join(lines)


def write_operator_status(path: Path, status: RetrievalRuntimeOperatorStatus) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_operator_status(status), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Export retrieval runtime operator status.")
    parser.add_argument("--boundary-report", type=Path, default=root / DEFAULT_RUNTIME_BOUNDARY_REPORT)
    parser.add_argument("--health-report", type=Path, default=root / DEFAULT_RUNTIME_HEALTH_REPORT)
    parser.add_argument("--enablement-report", type=Path, default=root / "kbs/retrieval/kb_production_semantic_retrieval_enablement_gate.v1.json")
    parser.add_argument("--output", type=Path, default=root / DEFAULT_OPERATOR_STATUS_EXPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_boundary_report(
        args.boundary_report,
        enablement_report_path=args.enablement_report,
        requested_adapter="bm25_authoritative",
    )
    health_report = build_runtime_health_surface_report(boundary_report_path=args.boundary_report)
    write_runtime_health_surface_report(args.health_report, health_report)
    status = build_operator_status(health_report_path=args.boundary_report)
    write_operator_status(args.output, status)
    print(f"[gate20c:operator-status] Wrote operator status export: {args.output}")
    print(f"[gate20c:operator-status] status={status.status}")
    print(f"[gate20c:operator-status] live_adapter={status.live_adapter}")
    print(f"[gate20c:operator-status] action_required={status.action_required}")
    print(f"[gate20c:operator-status] semantic_retrieval_enabled={_bool_text(status.semantic_retrieval_enabled)}")


if __name__ == "__main__":
    main()
