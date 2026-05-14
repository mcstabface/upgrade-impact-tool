from __future__ import annotations

from app.scripts.retrieval_runtime_status_bundle import main as build_status_bundle
from app.scripts.validate_retrieval_runtime_status_bundle import run_validation


def main() -> None:
    run_validation()
    build_status_bundle()
    print("[gate20f] Pipeline complete")
    print("[gate20f] Retrieval runtime status bundle preserves BM25-authoritative fail-closed posture")


if __name__ == "__main__":
    main()
