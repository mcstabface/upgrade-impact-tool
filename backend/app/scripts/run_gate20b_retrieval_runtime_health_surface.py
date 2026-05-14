from __future__ import annotations

from app.scripts.retrieval_runtime_health_surface import main as build_runtime_health_surface
from app.scripts.validate_retrieval_runtime_health_surface import run_validation


def main() -> None:
    run_validation()
    build_runtime_health_surface()
    print("[gate20b] Pipeline complete")
    print("[gate20b] Retrieval runtime health surface exposes BM25-authoritative fail-closed state")


if __name__ == "__main__":
    main()
