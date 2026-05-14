from __future__ import annotations

from app.scripts.retrieval_runtime_operator_status_export import main as export_operator_status
from app.scripts.validate_retrieval_runtime_operator_status_export import run_validation


def main() -> None:
    run_validation()
    export_operator_status()
    print("[gate20c] Pipeline complete")
    print("[gate20c] Retrieval runtime operator status export preserves BM25-authoritative fail-closed posture")


if __name__ == "__main__":
    main()
