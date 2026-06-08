#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_PATH="${1:-${ROOT_DIR}/artifacts/genti_review_workflow/genti_review_workflow_demo.db}"
EXPORT_DIR="${2:-${ROOT_DIR}/artifacts/genti_review_workflow/reports}"

bash "${ROOT_DIR}/scripts/verify_gate_21q_genti_seeded_schema.sh" "${DB_PATH}" >/dev/null
mkdir -p "${EXPORT_DIR}"

python3 - "${DB_PATH}" "${EXPORT_DIR}" <<'PY'
import csv
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(sys.argv[1])
EXPORT_DIR = Path(sys.argv[2])
BUG_ID = "BUG-136"
SCHEMA_VERSION = "genti_review_workflow_seeded_schema_v1"


def rows(cursor):
    return [dict(row) for row in cursor.fetchall()]


def write_csv(path, fieldnames, data):
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data)


def write_json(path, data):
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def write_markdown(path, title, rows_data, columns):
    with path.open("w", encoding="utf-8") as fh:
        fh.write(f"# {title}\n\n")
        fh.write("| " + " | ".join(columns) + " |\n")
        fh.write("|" + "|".join(["---" for _ in columns]) + "|\n")
        for row in rows_data:
            values = [str(row.get(column, "") if row.get(column, "") is not None else "").replace("\n", " ") for column in columns]
            fh.write("| " + " | ".join(values) + " |\n")


conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys=ON")

schema_version = conn.execute("SELECT schema_value FROM schema_metadata WHERE schema_key='schema_version'").fetchone()[0]
if schema_version != SCHEMA_VERSION:
    raise SystemExit(f"Unexpected schema version: {schema_version}")

mismatch_rows = rows(conn.execute("""
    SELECT
      be.canonical_bug_identifier AS bug_id,
      be.display_title,
      mp.mp_path,
      be.current_mismatch_state,
      mf.flag_type,
      COALESCE(mf.field_name, '') AS field_name,
      COALESCE(mf.pdf_value, '') AS pdf_value,
      COALESCE(mf.website_value, '') AS website_value,
      mf.review_status AS mismatch_review_status,
      rs.status_code AS current_status_code,
      rs.display_label AS current_status_label
    FROM bug_entries be
    JOIN mismatch_flags mf ON mf.bug_entry_id = be.bug_entry_id
    LEFT JOIN maintenance_packs mp ON mp.maintenance_pack_id = be.maintenance_pack_id
    LEFT JOIN review_statuses rs ON rs.review_status_id = be.current_review_status_id
    WHERE mf.flag_type <> 'MATCHED'
    ORDER BY mf.flag_type, be.canonical_bug_identifier, COALESCE(mf.field_name, '')
"""))

test_required_rows = rows(conn.execute("""
    SELECT
      be.canonical_bug_identifier AS bug_id,
      be.display_title,
      mp.mp_path,
      be.current_mismatch_state,
      be.review_priority,
      rs.status_code AS current_status_code,
      rs.display_label AS current_status_label
    FROM bug_entries be
    JOIN review_statuses rs ON rs.review_status_id = be.current_review_status_id
    LEFT JOIN maintenance_packs mp ON mp.maintenance_pack_id = be.maintenance_pack_id
    WHERE rs.status_code = 'TEST_REQUIRED'
    ORDER BY be.canonical_bug_identifier
"""))

bug_header = conn.execute("""
    SELECT
      be.bug_entry_id,
      be.canonical_bug_identifier AS bug_id,
      be.display_title,
      mp.mp_path,
      be.current_mismatch_state,
      be.review_priority,
      rs.status_code AS current_status_code,
      rs.display_label AS current_status_label,
      pbi.subsystem AS pdf_subsystem,
      pbi.title AS pdf_title,
      wbi.subsystem AS website_subsystem,
      wbi.title AS website_title
    FROM bug_entries be
    LEFT JOIN maintenance_packs mp ON mp.maintenance_pack_id = be.maintenance_pack_id
    LEFT JOIN review_statuses rs ON rs.review_status_id = be.current_review_status_id
    LEFT JOIN portfolio_bug_inventory pbi ON pbi.portfolio_bug_inventory_id = be.portfolio_bug_inventory_id
    LEFT JOIN website_bug_inventory wbi ON wbi.website_bug_inventory_id = be.website_bug_inventory_id
    WHERE be.canonical_bug_identifier = ?
""", (BUG_ID,)).fetchone()
if bug_header is None:
    raise SystemExit(f"Bug not found: {BUG_ID}")
bug_entry_id = int(bug_header["bug_entry_id"])

bug_detail = {
    "header": dict(bug_header),
    "mismatch_flags": rows(conn.execute("""
        SELECT flag_type, COALESCE(field_name, '') AS field_name, COALESCE(pdf_value, '') AS pdf_value,
               COALESCE(website_value, '') AS website_value, review_status
        FROM mismatch_flags
        WHERE bug_entry_id = ?
        ORDER BY flag_type, COALESCE(field_name, '')
    """, (bug_entry_id,))),
    "extracted_fields": rows(conn.execute("""
        SELECT field_name, field_value_type, field_value_text
        FROM bug_extracted_fields
        WHERE bug_entry_id = ?
        ORDER BY bug_extracted_field_id
    """, (bug_entry_id,))),
    "bug_pdf_artifacts": rows(conn.execute("""
        SELECT artifact_filename, artifact_storage_ref, source_page_start, source_page_end, extraction_status
        FROM bug_pdf_artifacts
        WHERE bug_entry_id = ?
        ORDER BY bug_pdf_artifact_id
    """, (bug_entry_id,))),
    "tags": rows(conn.execute("""
        SELECT td.tag_code, td.tag_name, bet.applied_by, bet.applied_utc
        FROM bug_entry_tags bet
        JOIN tag_dictionary td ON td.tag_id = bet.tag_id
        WHERE bet.bug_entry_id = ? AND bet.removed_utc IS NULL
        ORDER BY td.display_order
    """, (bug_entry_id,))),
    "notes": rows(conn.execute("""
        SELECT note_type, note_text, created_by, created_utc
        FROM bug_entry_notes
        WHERE bug_entry_id = ? AND is_deleted = 0
        ORDER BY created_utc, bug_entry_note_id
    """, (bug_entry_id,))),
}

audit_rows = rows(conn.execute("""
    SELECT
      COALESCE(be.canonical_bug_identifier, '') AS bug_id,
      ae.event_type,
      ae.entity_type,
      ae.entity_id,
      ae.event_payload_json,
      ae.created_by,
      ae.created_utc
    FROM audit_events ae
    LEFT JOIN bug_entries be ON be.bug_entry_id = ae.bug_entry_id
    ORDER BY ae.created_utc, ae.audit_event_id
"""))

files = {
    "mismatch_csv": EXPORT_DIR / "genti_mismatch_review.csv",
    "test_required_csv": EXPORT_DIR / "genti_test_required.csv",
    "bug_detail_json": EXPORT_DIR / "genti_bug_136_detail.json",
    "audit_csv": EXPORT_DIR / "genti_audit_history.csv",
    "mismatch_md": EXPORT_DIR / "genti_mismatch_review.md",
}

write_csv(
    files["mismatch_csv"],
    ["bug_id", "display_title", "mp_path", "current_mismatch_state", "flag_type", "field_name", "pdf_value", "website_value", "mismatch_review_status", "current_status_code", "current_status_label"],
    mismatch_rows,
)
write_csv(
    files["test_required_csv"],
    ["bug_id", "display_title", "mp_path", "current_mismatch_state", "review_priority", "current_status_code", "current_status_label"],
    test_required_rows,
)
write_json(files["bug_detail_json"], bug_detail)
write_csv(
    files["audit_csv"],
    ["bug_id", "event_type", "entity_type", "entity_id", "event_payload_json", "created_by", "created_utc"],
    audit_rows,
)
write_markdown(
    files["mismatch_md"],
    "Genti Mismatch Review",
    mismatch_rows,
    ["bug_id", "display_title", "mp_path", "flag_type", "field_name", "current_status_code"],
)

conn.close()

summary = {
    "schema_version": schema_version,
    "export_dir": str(EXPORT_DIR),
    "mismatch_rows": len(mismatch_rows),
    "test_required_rows": len(test_required_rows),
    "bug_detail_id": bug_detail["header"]["bug_id"],
    "bug_detail_fields": len(bug_detail["extracted_fields"]),
    "bug_detail_pdf_artifacts": len(bug_detail["bug_pdf_artifacts"]),
    "audit_rows": len(audit_rows),
    "files": {key: str(path) for key, path in sorted(files.items())},
}
print(json.dumps(summary, indent=2, sort_keys=True))
PY

python3 - "${EXPORT_DIR}" <<'PY'
import csv
import json
import sys
from pathlib import Path

EXPORT_DIR = Path(sys.argv[1])
files = {
    "mismatch_csv": EXPORT_DIR / "genti_mismatch_review.csv",
    "test_required_csv": EXPORT_DIR / "genti_test_required.csv",
    "bug_detail_json": EXPORT_DIR / "genti_bug_136_detail.json",
    "audit_csv": EXPORT_DIR / "genti_audit_history.csv",
    "mismatch_md": EXPORT_DIR / "genti_mismatch_review.md",
}

failures = []
def require(condition, message):
    if not condition:
        failures.append(message)

for label, path in files.items():
    require(path.exists(), f"missing export file: {label}")
    require(path.stat().st_size > 0, f"empty export file: {label}")

with files["mismatch_csv"].open("r", encoding="utf-8", newline="") as fh:
    mismatch_rows = list(csv.DictReader(fh))
with files["test_required_csv"].open("r", encoding="utf-8", newline="") as fh:
    test_required_rows = list(csv.DictReader(fh))
with files["audit_csv"].open("r", encoding="utf-8", newline="") as fh:
    audit_rows = list(csv.DictReader(fh))
with files["bug_detail_json"].open("r", encoding="utf-8") as fh:
    bug_detail = json.load(fh)
md_text = files["mismatch_md"].read_text(encoding="utf-8")

require(len(mismatch_rows) == 7, "mismatch export row count mismatch")
require(any(row["bug_id"] == "BUG-136" and row["flag_type"] == "FIELD_MISMATCH" for row in mismatch_rows), "BUG-136 mismatch missing from export")
require(len(test_required_rows) == 1, "test-required export row count mismatch")
require(test_required_rows[0]["bug_id"] == "BUG-136", "test-required export bug mismatch")
require(bug_detail["header"]["bug_id"] == "BUG-136", "bug detail export bug mismatch")
require(bug_detail["header"]["current_status_code"] == "TEST_REQUIRED", "bug detail export status mismatch")
require(len(bug_detail["extracted_fields"]) == 4, "bug detail extracted field count mismatch")
require(len(bug_detail["bug_pdf_artifacts"]) == 1, "bug detail PDF artifact count mismatch")
require(len(bug_detail["tags"]) == 1, "bug detail tag count mismatch")
require(len(bug_detail["notes"]) == 2, "bug detail note count mismatch")
require(len(audit_rows) == 6, "audit export row count mismatch")
require(any(row["event_type"] == "STATUS_CHANGED" for row in audit_rows), "STATUS_CHANGED missing from audit export")
require("Genti Mismatch Review" in md_text, "markdown export title missing")
require("BUG-136" in md_text, "BUG-136 missing from markdown export")

if failures:
    raise SystemExit("Gate 21S report/export validation failed:\n- " + "\n- ".join(failures))

print("Gate 21S report/export validation passed")
print(f"export_dir: {EXPORT_DIR}")
print(f"mismatch_export_rows: {len(mismatch_rows)}")
print(f"test_required_export_rows: {len(test_required_rows)}")
print(f"bug_detail_export_id: {bug_detail['header']['bug_id']}")
print(f"bug_detail_export_fields: {len(bug_detail['extracted_fields'])}")
print(f"audit_export_rows: {len(audit_rows)}")
print(f"export_files: {len(files)}")
PY
