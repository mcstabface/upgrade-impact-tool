from __future__ import annotations

from app.scripts.actual_corpus_prerequisite_regeneration import main as regenerate_prerequisites
from app.scripts.validate_actual_corpus_prerequisite_regeneration import run_validation


def main() -> None:
    run_validation()
    regenerate_prerequisites()
    print("[gate21g] Pipeline complete")
    print("[gate21g] Actual corpus prerequisite regeneration completed")


if __name__ == "__main__":
    main()
