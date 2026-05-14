from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from app.scripts.retrieval_runtime_operator_status_export import (
    build_operator_status,
    render_operator_status,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_boundary(path: Path, *, semantic_enabled: bool = False, fail_closed: bool = True) -> None:
    path.write_text(
        """{
  "bm25_authoritative": true,
  "fail_closed": %s,
  "hybrid_merge_enabled": false,
  "live_adapter": "bm25_authoritative",
  "report_version": "1",
  "selection": {
    "selected_adapter": "bm25_authoritative"
  },
  "semantic_retrieval_enabled": %s,
  "source_enablement_report": "kbs/retrieval/kb_production_semantic_retrieval_enablement_gate.v1.json",
  "status": "RETRIEVAL_RUNTIME_BOUNDARY_READY"
}
"""
        % ("true" if fail_closed else "false", "true" if semantic_enabled else "false"),
        encoding="utf-8",
    )


def test_healthy_operator_status() -> None:
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "boundary.json"
        _write_boundary(path)
        status = build_operator_status(health_report_path=path)
        _assert(status.status == "RETRIEVAL_RUNTIME_HEALTHY", status.status)
        _assert(status.live_adapter == "bm25_authoritative", status.live_adapter)
        _assert(status.action_required == "none", status.action_required)
        _assert(status.semantic_retrieval_enabled is False, "semantic retrieval must remain false")
        rendered = render_operator_status(status)
        _assert("Retrieval runtime is healthy" in rendered, rendered)
        _assert("| live_adapter | `bm25_authoritative` |" in rendered, rendered)
        _assert("| semantic_retrieval_enabled | `false` |" in rendered, rendered)


def test_unhealthy_operator_status_when_semantic_enabled() -> None:
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "boundary.json"
        _write_boundary(path, semantic_enabled=True)
        status = build_operator_status(health_report_path=path)
        _assert(status.status == "RETRIEVAL_RUNTIME_UNHEALTHY", status.status)
        _assert(status.action_required == "investigate_runtime_health", status.action_required)
        rendered = render_operator_status(status)
        _assert("Retrieval runtime is unhealthy" in rendered, rendered)
        _assert("| semantic_retrieval_enabled | `true` |" in rendered, rendered)


def test_unhealthy_operator_status_when_fail_open() -> None:
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "boundary.json"
        _write_boundary(path, fail_closed=False)
        status = build_operator_status(health_report_path=path)
        _assert(status.status == "RETRIEVAL_RUNTIME_UNHEALTHY", status.status)
        _assert(status.action_required == "investigate_runtime_health", status.action_required)
        rendered = render_operator_status(status)
        _assert("| fail_closed | `false` |" in rendered, rendered)


def run_validation() -> None:
    test_healthy_operator_status()
    test_unhealthy_operator_status_when_semantic_enabled()
    test_unhealthy_operator_status_when_fail_open()
    print("[gate20c:operator-status] OK")
    print("[gate20c:operator-status] healthy_status=exported")
    print("[gate20c:operator-status] semantic_enabled=action_required")
    print("[gate20c:operator-status] fail_open=action_required")
    print("[gate20c:operator-status] action_required=none")
    print("[gate20c:operator-status] semantic_retrieval_enabled=false")


if __name__ == "__main__":
    run_validation()
