from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from app.scripts.retrieval_runtime_adapter_boundary import write_runtime_boundary_report
from app.scripts.retrieval_runtime_health_surface import build_runtime_health_surface_report


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_healthy_boundary_report() -> None:
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "healthy_boundary.json"
        path.write_text(
            """{
  "bm25_authoritative": true,
  "disabled_adapters": [
    "semantic_vector",
    "hybrid_retrieval"
  ],
  "fail_closed": true,
  "hybrid_merge_enabled": false,
  "live_adapter": "bm25_authoritative",
  "report_version": "1",
  "selection": {
    "bm25_authoritative": true,
    "errors": [],
    "fail_closed": true,
    "hybrid_merge_enabled": false,
    "reason": "BM25_AUTHORITATIVE_DEFAULT",
    "requested_adapter": "bm25_authoritative",
    "selected_adapter": "bm25_authoritative",
    "semantic_retrieval_enabled": false,
    "status": "SELECTED"
  },
  "semantic_retrieval_enabled": false,
  "source_enablement_report": "kbs/retrieval/kb_production_semantic_retrieval_enablement_gate.v1.json",
  "status": "RETRIEVAL_RUNTIME_BOUNDARY_READY",
  "supported_adapters": [
    "bm25_authoritative"
  ]
}
""",
            encoding="utf-8",
        )
        report = build_runtime_health_surface_report(boundary_report_path=path)
        _assert(report.status == "RETRIEVAL_RUNTIME_HEALTHY", report.status)
        _assert(report.live_adapter == "bm25_authoritative", report.live_adapter)
        _assert(report.bm25_authoritative is True, "bm25_authoritative must be true")
        _assert(report.semantic_retrieval_enabled is False, "semantic retrieval must remain false")
        _assert(report.hybrid_merge_enabled is False, "hybrid merge must remain false")
        _assert(report.fail_closed is True, "fail_closed must be true")
        _assert(all(check.status == "PASS" for check in report.health_checks), "all health checks must pass")
        _assert(report.errors == [], f"unexpected errors: {report.errors}")


def test_unhealthy_if_semantic_enabled() -> None:
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "bad_boundary.json"
        path.write_text(
            """{
  "bm25_authoritative": true,
  "fail_closed": true,
  "hybrid_merge_enabled": false,
  "live_adapter": "bm25_authoritative",
  "report_version": "1",
  "selection": {
    "selected_adapter": "bm25_authoritative"
  },
  "semantic_retrieval_enabled": true,
  "source_enablement_report": "kbs/retrieval/kb_production_semantic_retrieval_enablement_gate.v1.json",
  "status": "RETRIEVAL_RUNTIME_BOUNDARY_READY"
}
""",
            encoding="utf-8",
        )
        report = build_runtime_health_surface_report(boundary_report_path=path)
        _assert(report.status == "RETRIEVAL_RUNTIME_UNHEALTHY", report.status)
        _assert(any("semantic_retrieval_enabled" in error for error in report.errors), report.errors)


def test_unhealthy_if_not_fail_closed() -> None:
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "bad_boundary.json"
        path.write_text(
            """{
  "bm25_authoritative": true,
  "fail_closed": false,
  "hybrid_merge_enabled": false,
  "live_adapter": "bm25_authoritative",
  "report_version": "1",
  "selection": {
    "selected_adapter": "bm25_authoritative"
  },
  "semantic_retrieval_enabled": false,
  "source_enablement_report": "kbs/retrieval/kb_production_semantic_retrieval_enablement_gate.v1.json",
  "status": "RETRIEVAL_RUNTIME_BOUNDARY_READY"
}
""",
            encoding="utf-8",
        )
        report = build_runtime_health_surface_report(boundary_report_path=path)
        _assert(report.status == "RETRIEVAL_RUNTIME_UNHEALTHY", report.status)
        _assert(any("fail_closed" in error for error in report.errors), report.errors)


def run_validation() -> None:
    test_healthy_boundary_report()
    test_unhealthy_if_semantic_enabled()
    test_unhealthy_if_not_fail_closed()
    print("[gate20b:runtime-health] OK")
    print("[gate20b:runtime-health] healthy_boundary=pass")
    print("[gate20b:runtime-health] semantic_enabled=unhealthy")
    print("[gate20b:runtime-health] fail_open=unhealthy")
    print("[gate20b:runtime-health] bm25_authoritative=true")
    print("[gate20b:runtime-health] semantic_retrieval_enabled=false")


if __name__ == "__main__":
    run_validation()
