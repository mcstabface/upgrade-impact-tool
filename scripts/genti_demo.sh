#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_DB_PATH="${ROOT_DIR}/artifacts/genti_review_workflow/genti_review_workflow_demo.db"
DEFAULT_REPORT_DIR="${ROOT_DIR}/artifacts/genti_review_workflow/reports"
DEFAULT_ARTIFACT_DIR="${ROOT_DIR}/artifacts/genti_review_workflow"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/genti_demo.sh prepare [db_path]
  bash scripts/genti_demo.sh query [db_path]
  bash scripts/genti_demo.sh reports [db_path] [report_dir]
  bash scripts/genti_demo.sh summary [db_path] [report_dir]
  bash scripts/genti_demo.sh all [db_path] [report_dir]
  bash scripts/genti_demo.sh quiet [db_path] [report_dir]
  bash scripts/genti_demo.sh show-files [db_path] [report_dir]
  bash scripts/genti_demo.sh clean

Commands:
  prepare    Create/reset the seeded Genti workflow demo database.
  query      Validate deterministic query/view output over the seeded database.
  reports    Generate and validate deterministic report exports.
  summary    Print a compact demo artifact summary.
  all        Run prepare, query, reports, then summary.
  quiet      Run the full demo path with only the compact summary output.
  show-files Print expected generated artifact paths.
  clean      Remove generated local demo artifacts.

Defaults:
  db_path    artifacts/genti_review_workflow/genti_review_workflow_demo.db
  report_dir artifacts/genti_review_workflow/reports
EOF
}

command="${1:-}"
if [[ -z "${command}" || "${command}" == "-h" || "${command}" == "--help" ]]; then
  usage
  exit 0
fi
shift || true

DB_PATH="${1:-${DEFAULT_DB_PATH}}"
REPORT_DIR="${2:-${DEFAULT_REPORT_DIR}}"

prepare() {
  bash "${ROOT_DIR}/scripts/verify_gate_21q_genti_seeded_schema.sh" "${DB_PATH}"
}

query() {
  bash "${ROOT_DIR}/scripts/verify_gate_21r_genti_query_views.sh" "${DB_PATH}"
}

reports() {
  bash "${ROOT_DIR}/scripts/verify_gate_21s_genti_report_exports.sh" "${DB_PATH}" "${REPORT_DIR}"
}

summary() {
  python3 - "${DB_PATH}" "${REPORT_DIR}" <<'PY'
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(sys.argv[1])
REPORT_DIR = Path(sys.argv[2])

if not DB_PATH.exists():
    raise SystemExit(f"Demo database not found: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys=ON")

def scalar(sql, params=()):
    return int(conn.execute(sql, params).fetchone()[0])

schema_version = conn.execute("SELECT schema_value FROM schema_metadata WHERE schema_key='schema_version'").fetchone()[0]
summary_rows = {
    "schema_version": schema_version,
    "db_path": str(DB_PATH),
    "report_dir": str(REPORT_DIR),
    "portfolio_uploads": scalar("SELECT COUNT(*) FROM portfolio_uploads"),
    "bug_entries": scalar("SELECT COUNT(*) FROM bug_entries"),
    "mismatch_flags": scalar("SELECT COUNT(*) FROM mismatch_flags"),
    "pdf_only_mismatches": scalar("SELECT COUNT(*) FROM mismatch_flags WHERE flag_type='PDF_ONLY'"),
    "website_only_mismatches": scalar("SELECT COUNT(*) FROM mismatch_flags WHERE flag_type='WEBSITE_ONLY'"),
    "field_mismatches": scalar("SELECT COUNT(*) FROM mismatch_flags WHERE flag_type='FIELD_MISMATCH'"),
    "test_required_entries": scalar("""
        SELECT COUNT(*)
        FROM bug_entries be
        JOIN review_statuses rs ON rs.review_status_id = be.current_review_status_id
        WHERE rs.status_code='TEST_REQUIRED'
    """),
    "bug_pdf_artifacts": scalar("SELECT COUNT(*) FROM bug_pdf_artifacts"),
    "bug_extracted_fields": scalar("SELECT COUNT(*) FROM bug_extracted_fields"),
    "audit_events": scalar("SELECT COUNT(*) FROM audit_events"),
}
conn.close()

report_files = [
    REPORT_DIR / "genti_mismatch_review.csv",
    REPORT_DIR / "genti_test_required.csv",
    REPORT_DIR / "genti_bug_136_detail.json",
    REPORT_DIR / "genti_audit_history.csv",
    REPORT_DIR / "genti_mismatch_review.md",
]
summary_rows["report_files_present"] = sum(1 for path in report_files if path.exists() and path.stat().st_size > 0)
summary_rows["report_files_expected"] = len(report_files)

print("Genti demo summary")
for key in sorted(summary_rows):
    print(f"{key}: {summary_rows[key]}")
PY
}

show_files() {
  cat <<EOF
Genti demo generated artifacts

database:
${DB_PATH}

reports:
${REPORT_DIR}/genti_mismatch_review.csv
${REPORT_DIR}/genti_test_required.csv
${REPORT_DIR}/genti_bug_136_detail.json
${REPORT_DIR}/genti_audit_history.csv
${REPORT_DIR}/genti_mismatch_review.md
EOF
}

clean() {
  rm -rf "${DEFAULT_ARTIFACT_DIR}"
  echo "removed: ${DEFAULT_ARTIFACT_DIR}"
}

case "${command}" in
  prepare)
    prepare
    ;;
  query)
    query
    ;;
  reports)
    reports
    ;;
  summary)
    summary
    ;;
  all)
    prepare >/dev/null
    query
    reports
    summary
    ;;
  quiet)
    prepare >/dev/null
    query >/dev/null
    reports >/dev/null
    summary
    ;;
  show-files)
    show_files
    ;;
  clean)
    clean
    ;;
  *)
    echo "Unknown command: ${command}" >&2
    usage >&2
    exit 2
    ;;
esac
