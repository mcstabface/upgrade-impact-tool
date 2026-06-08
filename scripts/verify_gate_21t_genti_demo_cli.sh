#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_PATH="${1:-${ROOT_DIR}/artifacts/genti_review_workflow/genti_review_workflow_demo.db}"
REPORT_DIR="${2:-${ROOT_DIR}/artifacts/genti_review_workflow/reports}"
SUMMARY_OUT="$(mktemp)"
trap 'rm -f "${SUMMARY_OUT}"' EXIT

bash "${ROOT_DIR}/scripts/genti_demo.sh" prepare "${DB_PATH}" >/dev/null
bash "${ROOT_DIR}/scripts/genti_demo.sh" query "${DB_PATH}" >/dev/null
bash "${ROOT_DIR}/scripts/genti_demo.sh" reports "${DB_PATH}" "${REPORT_DIR}" >/dev/null
bash "${ROOT_DIR}/scripts/genti_demo.sh" summary "${DB_PATH}" "${REPORT_DIR}" > "${SUMMARY_OUT}"

python3 - "${SUMMARY_OUT}" <<'PY'
import sys
from pathlib import Path

summary_path = Path(sys.argv[1])
text = summary_path.read_text(encoding="utf-8")
values = {}
for line in text.splitlines():
    if ": " in line:
        key, value = line.split(": ", 1)
        values[key] = value

failures = []
def require(condition, message):
    if not condition:
        failures.append(message)

require("Genti demo summary" in text, "summary title missing")
require(values.get("schema_version") == "genti_review_workflow_seeded_schema_v1", "schema version mismatch")
require(values.get("portfolio_uploads") == "1", "portfolio count mismatch")
require(values.get("bug_entries") == "11", "bug count mismatch")
require(values.get("mismatch_flags") == "11", "mismatch count mismatch")
require(values.get("pdf_only_mismatches") == "3", "PDF-only mismatch count mismatch")
require(values.get("website_only_mismatches") == "2", "Web-site-only mismatch count mismatch")
require(values.get("field_mismatches") == "2", "field mismatch count mismatch")
require(values.get("test_required_entries") == "1", "test-required count mismatch")
require(values.get("bug_pdf_artifacts") == "3", "Bug PDF artifact count mismatch")
require(values.get("bug_extracted_fields") == "10", "extracted field count mismatch")
require(values.get("audit_events") == "6", "audit event count mismatch")
require(values.get("report_files_present") == "5", "report files present mismatch")
require(values.get("report_files_expected") == "5", "report files expected mismatch")

if failures:
    raise SystemExit("Gate 21T demo CLI validation failed:\n- " + "\n- ".join(failures))

print("Gate 21T demo CLI validation passed")
for key in [
    "bug_entries",
    "mismatch_flags",
    "test_required_entries",
    "bug_pdf_artifacts",
    "audit_events",
    "report_files_present",
]:
    print(f"{key}: {values[key]}")
PY
