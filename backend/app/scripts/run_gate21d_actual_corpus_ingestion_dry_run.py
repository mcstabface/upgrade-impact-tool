from __future__ import annotations

from app.scripts.actual_corpus_ingestion_dry_run import main as run_dry_run
from app.scripts.validate_actual_corpus_ingestion_dry_run import run_validation


def main() -> None:
    run_validation()
    run_dry_run()
    print("[gate21d] Pipeline complete")
    print("[gate21d] Actual corpus ingestion dry run completed for kbs/raw")


if __name__ == "__main__":
    main()
