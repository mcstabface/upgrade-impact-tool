from __future__ import annotations

from app.scripts.actual_corpus_search_context_dry_run import main as run_dry_run
from app.scripts.validate_actual_corpus_search_context_dry_run import run_validation


def main() -> None:
    run_validation()
    run_dry_run()
    print("[gate21f] Pipeline complete")
    print("[gate21f] Actual corpus search-context extraction dry run completed")


if __name__ == "__main__":
    main()
