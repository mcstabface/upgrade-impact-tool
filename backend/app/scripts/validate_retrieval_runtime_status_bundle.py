from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from app.scripts.retrieval_runtime_status_bundle import build_status_bundle


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_enablement(path: Path, *, semantic_enabled: bool = False, fail_closed: bool = True) -> None:
    path.write_text(
        """{
  "bm25_authoritative": true,
  "fail_closed": %s,
  "hybrid_merge_enabled": false,
  "production_semantic_retrieval_enabled": %s,
  "report_version": "1",
  "status": "%s",
  "vector_retrieval_authoritative": false
}
"""
        % (
            "true" if fail_closed else "false",
            "true" if semantic_enabled else "false",
            "PRODUCTION_SEMANTIC_RETRIEVAL_DISABLED" if not semantic_enabled else "PRODUCTION_SEMANTIC_RETRIEVAL_ENABLED",
        ),
        encoding="utf-8",
    )


def test_healthy_status_bundle() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        enablement = root / "enablement.json"
        boundary = root / "boundary.json"
        health = root / "health.json"
        operator = root / "operator.md"
        _write_enablement(enablement)
        bundle = build_status_bundle(
            enablement_report_path=enablement,
            boundary_report_path=boundary,
            health_report_path=health,
            operator_status_path=operator,
        )
        _assert(bundle.status == "RETRIEVAL_RUNTIME_STATUS_BUNDLE_READY", bundle.status)
        _assert(bundle.boundary_status == "RETRIEVAL_RUNTIME_BOUNDARY_READY", bundle.boundary_status)
        _assert(bundle.health_status == "RETRIEVAL_RUNTIME_HEALTHY", bundle.health_status)
        _assert(bundle.operator_action_required == "none", bundle.operator_action_required)
        _assert(bundle.live_adapter == "bm25_authoritative", bundle.live_adapter)
        _assert(bundle.semantic_retrieval_enabled is False, "semantic retrieval must remain false")
        _assert(bundle.errors == [], bundle.errors)
        _assert(boundary.exists(), "boundary report must be written")
        _assert(health.exists(), "health report must be written")
        _assert(operator.exists(), "operator status must be written")


def test_unhealthy_if_enablement_semantic_enabled() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        enablement = root / "enablement.json"
        boundary = root / "boundary.json"
        health = root / "health.json"
        operator = root / "operator.md"
        _write_enablement(enablement, semantic_enabled=True)
        bundle = build_status_bundle(
            enablement_report_path=enablement,
            boundary_report_path=boundary,
            health_report_path=health,
            operator_status_path=operator,
        )
        _assert(bundle.status == "RETRIEVAL_RUNTIME_STATUS_BUNDLE_UNHEALTHY", bundle.status)
        _assert(bundle.boundary_status == "RETRIEVAL_RUNTIME_BOUNDARY_REFUSED", bundle.boundary_status)
        _assert(bundle.health_status == "RETRIEVAL_RUNTIME_UNHEALTHY", bundle.health_status)
        _assert(bundle.operator_action_required == "investigate_runtime_health", bundle.operator_action_required)
        _assert(bundle.errors, "unhealthy bundle must include errors")


def test_unhealthy_if_enablement_fail_open() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        enablement = root / "enablement.json"
        boundary = root / "boundary.json"
        health = root / "health.json"
        operator = root / "operator.md"
        _write_enablement(enablement, fail_closed=False)
        bundle = build_status_bundle(
            enablement_report_path=enablement,
            boundary_report_path=boundary,
            health_report_path=health,
            operator_status_path=operator,
        )
        _assert(bundle.status == "RETRIEVAL_RUNTIME_STATUS_BUNDLE_UNHEALTHY", bundle.status)
        _assert(bundle.boundary_status == "RETRIEVAL_RUNTIME_BOUNDARY_REFUSED", bundle.boundary_status)
        _assert(bundle.health_status == "RETRIEVAL_RUNTIME_UNHEALTHY", bundle.health_status)
        _assert(bundle.operator_action_required == "investigate_runtime_health", bundle.operator_action_required)
        _assert(bundle.errors, "unhealthy bundle must include errors")


def run_validation() -> None:
    test_healthy_status_bundle()
    test_unhealthy_if_enablement_semantic_enabled()
    test_unhealthy_if_enablement_fail_open()
    print("[gate20f:status-bundle] OK")
    print("[gate20f:status-bundle] healthy_bundle=ready")
    print("[gate20f:status-bundle] semantic_enabled=unhealthy")
    print("[gate20f:status-bundle] fail_open=unhealthy")
    print("[gate20f:status-bundle] live_adapter=bm25_authoritative")
    print("[gate20f:status-bundle] semantic_retrieval_enabled=false")


if __name__ == "__main__":
    run_validation()
