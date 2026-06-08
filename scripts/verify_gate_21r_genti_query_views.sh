#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_PATH="${1:-${ROOT_DIR}/artifacts/genti_review_workflow/genti_review_workflow_demo.db}"
VIEW_JSON="$(mktemp)"
trap 'rm -f "${VIEW_JSON}"' EXIT

bash "${ROOT_DIR}/scripts/verify_gate_21q_genti_seeded_schema.sh" "${DB_PATH}" >/dev/null

python3 - "${DB_PATH}" > "${VIEW_JSON}" <<'PY'
import json
import sqlite3
import sys

DB_PATH = sys.argv[1]
BUG_ID = "BUG-136"


def rows(cursor):
    return [dict(row) for row in cursor.fetchall()]


def scalar(conn, sql, params=()):
    return int(conn.execute(sql, params).fetchone()[0])


conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys=ON")

schema_version = conn.execute(
    "SELECT schema_value FROM schema_metadata WHERE schema_key = 'schema_version'"
).fetchone()[0]

dashboard = {
    "portfolio_uploads": scalar(conn, "SELECT COUNT(*) FROM portfolio_uploads"),
    "bug_entries": scalar(conn, "SELECT COUNT(*) FROM bug_entries"),
    "mismatch_flags": scalar(conn, "SELECT COUNT(*) FROM mismatch_flags"),
    "open_mismatch_flags": scalar(conn, "SELECT COUNT(*) FROM mismatch_flags WHERE review_status = 'OPEN'"),
    "bug_pdf_artifacts": scalar(conn, "SELECT COUNT(*) FROM bug_pdf_artifacts"),
    "bug_extracted_fields": scalar(conn, "SELECT COUNT(*) FROM bug_extracted_fields"),
    "audit_events": scalar(conn, "SELECT COUNT(*) FROM audit_events"),
    "mismatch_counts": rows(conn.execute("""
        SELECT flag_type, COUNT(*) AS count
        FROM mismatch_flags
        GROUP BY flag_type
        ORDER BY flag_type
    """)),
    "status_counts": rows(conn.execute("""
        SELECT rs.status_code, rs.display_label, COUNT(be.bug_entry_id) AS count
        FROM review_statuses rs
        LEFT JOIN bug_entries be ON be.current_review_status_id = rs.review_status_id
        GROUP BY rs.review_status_id, rs.status_code, rs.display_label, rs.display_order
        ORDER BY rs.display_order
    """)),
    "maintenance_pack_counts": rows(conn.execute("""
        SELECT mp.mp_code, mp.mp_path, COUNT(be.bug_entry_id) AS bug_count
        FROM maintenance_packs mp
        LEFT JOIN bug_entries be ON be.maintenance_pack_id = mp.maintenance_pack_id
        GROUP BY mp.maintenance_pack_id, mp.mp_code, mp.mp_path, mp.display_order
        ORDER BY mp.display_order
    """)),
}

mismatch_review = rows(conn.execute("""
    SELECT
      be.canonical_bug_identifier AS bug_id,
      be.display_title,
      mp.mp_path,
      be.current_mismatch_state,
      mf.flag_type,
      mf.field_name,
      mf.pdf_value,
      mf.website_value,
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

header = conn.execute("""
    SELECT
      be.bug_entry_id,
      be.canonical_bug_identifier AS bug_id,
      be.display_title,
      be.current_mismatch_state,
      be.review_priority,
      mp.mp_path,
      rs.status_code AS current_status_code,
      rs.display_label AS current_status_label,
      pbi.source_bug_identifier AS pdf_bug_id,
      pbi.subsystem AS pdf_subsystem,
      pbi.title AS pdf_title,
      wbi.source_bug_identifier AS website_bug_id,
      wbi.subsystem AS website_subsystem,
      wbi.title AS website_title
    FROM bug_entries be
    LEFT JOIN maintenance_packs mp ON mp.maintenance_pack_id = be.maintenance_pack_id
    LEFT JOIN review_statuses rs ON rs.review_status_id = be.current_review_status_id
    LEFT JOIN portfolio_bug_inventory pbi ON pbi.portfolio_bug_inventory_id = be.portfolio_bug_inventory_id
    LEFT JOIN website_bug_inventory wbi ON wbi.website_bug_inventory_id = be.website_bug_inventory_id
    WHERE be.canonical_bug_identifier = ?
""", (BUG_ID,)).fetchone()
if header is None:
    raise SystemExit(f"Bug not found: {BUG_ID}")

bug_entry_id = int(header["bug_entry_id"])
bug_detail = {
    "header": dict(header),
    "mismatch_flags": rows(conn.execute("""
        SELECT flag_type, field_name, pdf_value, website_value, review_status
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
        ORDER BY td.display_order, td.tag_code
    """, (bug_entry_id,))),
    "notes": rows(conn.execute("""
        SELECT note_type, note_text, created_by, created_utc
        FROM bug_entry_notes
        WHERE bug_entry_id = ? AND is_deleted = 0
        ORDER BY created_utc, bug_entry_note_id
    """, (bug_entry_id,))),
    "status_history": rows(conn.execute("""
        SELECT from_rs.status_code AS from_status_code, to_rs.status_code AS to_status_code,
               h.change_reason, h.comment_text, h.changed_by, h.changed_utc
        FROM bug_entry_status_history h
        LEFT JOIN review_statuses from_rs ON from_rs.review_status_id = h.from_review_status_id
        JOIN review_statuses to_rs ON to_rs.review_status_id = h.to_review_status_id
        WHERE h.bug_entry_id = ?
        ORDER BY h.changed_utc, h.bug_entry_status_history_id
    """, (bug_entry_id,))),
    "audit_events": rows(conn.execute("""
        SELECT event_type, entity_type, entity_id, event_payload_json, created_by, created_utc
        FROM audit_events
        WHERE bug_entry_id = ?
        ORDER BY created_utc, audit_event_id
    """, (bug_entry_id,))),
}

workflow = {
    "status_history_rows": scalar(conn, "SELECT COUNT(*) FROM bug_entry_status_history WHERE bug_entry_id = ?", (bug_entry_id,)),
    "active_tag_rows": scalar(conn, "SELECT COUNT(*) FROM bug_entry_tags WHERE bug_entry_id = ? AND removed_utc IS NULL", (bug_entry_id,)),
    "note_rows": scalar(conn, "SELECT COUNT(*) FROM bug_entry_notes WHERE bug_entry_id = ? AND is_deleted = 0", (bug_entry_id,)),
    "audit_event_rows": scalar(conn, "SELECT COUNT(*) FROM audit_events WHERE bug_entry_id = ?", (bug_entry_id,)),
}

print(json.dumps({
    "schema_version": schema_version,
    "selected_bug_id": BUG_ID,
    "dashboard_summary": dashboard,
    "mismatch_review": mismatch_review,
    "bug_detail": bug_detail,
    "workflow_summary": workflow,
}, indent=2, sort_keys=True))
conn.close()
PY

python3 - "${VIEW_JSON}" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as fh:
    data = json.load(fh)

failures = []
def require(condition, message):
    if not condition:
        failures.append(message)

dashboard = data["dashboard_summary"]
mismatch_rows = data["mismatch_review"]
detail = data["bug_detail"]
workflow = data["workflow_summary"]

require(data["schema_version"] == "genti_review_workflow_seeded_schema_v1", "unexpected schema version")
require(data["selected_bug_id"] == "BUG-136", "unexpected selected bug")
require(dashboard["portfolio_uploads"] == 1, "dashboard portfolio count mismatch")
require(dashboard["bug_entries"] == 11, "dashboard bug count mismatch")
require(dashboard["bug_pdf_artifacts"] == 3, "dashboard Bug PDF count mismatch")
require(dashboard["audit_events"] == 6, "dashboard audit count mismatch")
flag_counts = {row["flag_type"]: row["count"] for row in dashboard["mismatch_counts"]}
require(flag_counts.get("PDF_ONLY") == 3, "PDF_ONLY dashboard count mismatch")
require(flag_counts.get("WEBSITE_ONLY") == 2, "WEBSITE_ONLY dashboard count mismatch")
require(flag_counts.get("FIELD_MISMATCH") == 2, "FIELD_MISMATCH dashboard count mismatch")
require(len(mismatch_rows) == 7, "expected seven non-matched mismatch review rows")
require(any(row["bug_id"] == "BUG-136" and row["flag_type"] == "FIELD_MISMATCH" for row in mismatch_rows), "BUG-136 field mismatch missing")
header = detail["header"]
require(header["bug_id"] == "BUG-136", "detail bug id mismatch")
require(header["current_status_code"] == "TEST_REQUIRED", "detail status mismatch")
require(header["current_mismatch_state"] == "FIELD_MISMATCH", "detail mismatch state mismatch")
require(len(detail["extracted_fields"]) >= 4, "detail extracted fields missing")
require(len(detail["bug_pdf_artifacts"]) == 1, "detail Bug PDF artifact missing")
require(len(detail["tags"]) == 1, "detail active tag missing")
require(detail["tags"][0]["tag_code"] == "NEEDS_VALIDATION", "detail tag mismatch")
require(len(detail["notes"]) == 2, "detail notes mismatch")
require(len(detail["status_history"]) == 1, "detail status history mismatch")
require(len(detail["audit_events"]) >= 4, "detail audit events missing")
require(workflow["status_history_rows"] == 1, "workflow status history count mismatch")
require(workflow["active_tag_rows"] == 1, "workflow active tag count mismatch")
require(workflow["note_rows"] == 2, "workflow note count mismatch")
require(workflow["audit_event_rows"] >= 4, "workflow audit count mismatch")

if failures:
    raise SystemExit("Gate 21R query/view validation failed:\n- " + "\n- ".join(failures))

print("Gate 21R query/view validation passed")
print(f"dashboard_bug_entries: {dashboard['bug_entries']}")
print(f"dashboard_mismatch_flags: {dashboard['mismatch_flags']}")
print(f"mismatch_review_rows: {len(mismatch_rows)}")
print(f"bug_detail_id: {header['bug_id']}")
print(f"bug_detail_status: {header['current_status_code']}")
print(f"bug_detail_extracted_fields: {len(detail['extracted_fields'])}")
print(f"bug_detail_pdf_artifacts: {len(detail['bug_pdf_artifacts'])}")
print(f"workflow_status_history_rows: {workflow['status_history_rows']}")
print(f"workflow_active_tag_rows: {workflow['active_tag_rows']}")
print(f"workflow_note_rows: {workflow['note_rows']}")
print(f"workflow_audit_event_rows: {workflow['audit_event_rows']}")
PY
