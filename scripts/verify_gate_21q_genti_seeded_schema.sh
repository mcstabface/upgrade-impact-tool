#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_PATH="${1:-${ROOT_DIR}/artifacts/genti_review_workflow/genti_review_workflow_demo.db}"

python3 - "${DB_PATH}" <<'PY'
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = sys.argv[1]
SCHEMA_VERSION = "genti_review_workflow_seeded_schema_v1"
SEED_UTC = 1772748800
SYSTEM_ACTOR = "gate_21q_seed"
REVIEWER_ACTOR = "demo_reviewer"
STATUSES = [
    (1, "NEW", "New"),
    (2, "NEEDS_FURTHER_REVIEW", "Needs Further Review"),
    (3, "TEST_REQUIRED", "Test Required"),
    (4, "TEST_DEFERRED", "Test Deferred"),
    (5, "CONFIRMED", "Confirmed"),
    (6, "NA", "N/A"),
    (7, "BLOCKED", "Blocked"),
    (8, "RESOLVED", "Resolved"),
]
TAGS = [
    (1, "Needs Validation", "NEEDS_VALIDATION"),
    (2, "Regression Risk", "REGRESSION_RISK"),
    (3, "Customer Visible", "CUSTOMER_VISIBLE"),
    (4, "Testing Candidate", "TESTING_CANDIDATE"),
    (5, "Documentation Check", "DOCUMENTATION_CHECK"),
]


def h(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def count(conn, sql, params=()):
    return int(conn.execute(sql, params).fetchone()[0])


Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Reset must be idempotent against an existing generated database. Disable
# foreign key enforcement only during table teardown, then re-enable it before
# creating and seeding the schema so all validation still runs with FK checks on.
conn.execute("PRAGMA foreign_keys=OFF")
for table in [
    "audit_events",
    "bug_extracted_fields",
    "bug_pdf_artifacts",
    "bug_entry_notes",
    "bug_entry_tags",
    "tag_dictionary",
    "bug_entry_status_history",
    "review_statuses",
    "mismatch_flags",
    "bug_entries",
    "website_bug_inventory",
    "portfolio_bug_inventory",
    "maintenance_packs",
    "portfolio_uploads",
    "schema_metadata",
]:
    conn.execute(f"DROP TABLE IF EXISTS {table}")
conn.commit()
conn.execute("PRAGMA foreign_keys=ON")

conn.executescript(
    """
    CREATE TABLE schema_metadata(schema_key TEXT PRIMARY KEY, schema_value TEXT NOT NULL);
    CREATE TABLE portfolio_uploads(
      portfolio_upload_id INTEGER PRIMARY KEY, portfolio_name TEXT NOT NULL, source_filename TEXT NOT NULL,
      content_type TEXT NOT NULL, file_size_bytes INTEGER NOT NULL, source_sha256 TEXT NOT NULL UNIQUE,
      upload_status TEXT NOT NULL, uploaded_by TEXT NOT NULL, uploaded_utc INTEGER NOT NULL, processed_utc INTEGER);
    CREATE TABLE maintenance_packs(
      maintenance_pack_id INTEGER PRIMARY KEY, parent_maintenance_pack_id INTEGER REFERENCES maintenance_packs,
      mp_code TEXT NOT NULL UNIQUE, mp_label TEXT NOT NULL, mp_path TEXT NOT NULL, display_order INTEGER NOT NULL,
      is_active INTEGER NOT NULL, created_utc INTEGER NOT NULL);
    CREATE TABLE portfolio_bug_inventory(
      portfolio_bug_inventory_id INTEGER PRIMARY KEY, portfolio_upload_id INTEGER NOT NULL REFERENCES portfolio_uploads,
      source_bug_identifier TEXT NOT NULL, maintenance_pack_path TEXT NOT NULL, subsystem TEXT NOT NULL, title TEXT NOT NULL,
      description_text TEXT, steps_text TEXT, source_page_start INTEGER, source_page_end INTEGER,
      raw_extracted_json TEXT NOT NULL, extraction_status TEXT NOT NULL, created_utc INTEGER NOT NULL);
    CREATE TABLE website_bug_inventory(
      website_bug_inventory_id INTEGER PRIMARY KEY, website_source_id TEXT NOT NULL, source_url TEXT NOT NULL,
      source_bug_identifier TEXT NOT NULL, maintenance_pack_path TEXT NOT NULL, subsystem TEXT NOT NULL, title TEXT NOT NULL,
      description_text TEXT, raw_extracted_json TEXT NOT NULL, import_status TEXT NOT NULL, imported_utc INTEGER NOT NULL);
    CREATE TABLE review_statuses(
      review_status_id INTEGER PRIMARY KEY, status_code TEXT NOT NULL UNIQUE, display_label TEXT NOT NULL,
      display_order INTEGER NOT NULL, is_active INTEGER NOT NULL, created_utc INTEGER NOT NULL);
    CREATE TABLE bug_entries(
      bug_entry_id INTEGER PRIMARY KEY, canonical_bug_identifier TEXT NOT NULL UNIQUE, display_title TEXT NOT NULL,
      current_review_status_id INTEGER REFERENCES review_statuses, maintenance_pack_id INTEGER REFERENCES maintenance_packs,
      portfolio_bug_inventory_id INTEGER REFERENCES portfolio_bug_inventory, website_bug_inventory_id INTEGER REFERENCES website_bug_inventory,
      current_mismatch_state TEXT NOT NULL, review_priority TEXT NOT NULL, is_active INTEGER NOT NULL,
      created_utc INTEGER NOT NULL, created_by TEXT NOT NULL, updated_utc INTEGER NOT NULL, updated_by TEXT NOT NULL);
    CREATE TABLE mismatch_flags(
      mismatch_flag_id INTEGER PRIMARY KEY, bug_entry_id INTEGER NOT NULL REFERENCES bug_entries, flag_type TEXT NOT NULL,
      field_name TEXT, pdf_value TEXT, website_value TEXT, severity TEXT NOT NULL, system_generated INTEGER NOT NULL,
      review_status TEXT NOT NULL, reviewed_by TEXT, reviewed_utc INTEGER, created_utc INTEGER NOT NULL);
    CREATE TABLE bug_entry_status_history(
      bug_entry_status_history_id INTEGER PRIMARY KEY, bug_entry_id INTEGER NOT NULL REFERENCES bug_entries,
      from_review_status_id INTEGER REFERENCES review_statuses, to_review_status_id INTEGER NOT NULL REFERENCES review_statuses,
      change_reason TEXT, comment_text TEXT, changed_by TEXT NOT NULL, changed_utc INTEGER NOT NULL);
    CREATE TABLE tag_dictionary(
      tag_id INTEGER PRIMARY KEY, tag_name TEXT NOT NULL UNIQUE, tag_code TEXT NOT NULL UNIQUE,
      display_order INTEGER NOT NULL, is_active INTEGER NOT NULL, created_by TEXT NOT NULL, created_utc INTEGER NOT NULL);
    CREATE TABLE bug_entry_tags(
      bug_entry_tag_id INTEGER PRIMARY KEY, bug_entry_id INTEGER NOT NULL REFERENCES bug_entries, tag_id INTEGER NOT NULL REFERENCES tag_dictionary,
      applied_by TEXT NOT NULL, applied_utc INTEGER NOT NULL, removed_by TEXT, removed_utc INTEGER);
    CREATE TABLE bug_entry_notes(
      bug_entry_note_id INTEGER PRIMARY KEY, bug_entry_id INTEGER NOT NULL REFERENCES bug_entries, note_text TEXT NOT NULL,
      note_type TEXT NOT NULL, created_by TEXT NOT NULL, created_utc INTEGER NOT NULL, is_deleted INTEGER NOT NULL);
    CREATE TABLE bug_pdf_artifacts(
      bug_pdf_artifact_id INTEGER PRIMARY KEY, bug_entry_id INTEGER NOT NULL REFERENCES bug_entries,
      portfolio_upload_id INTEGER NOT NULL REFERENCES portfolio_uploads, portfolio_bug_inventory_id INTEGER NOT NULL REFERENCES portfolio_bug_inventory,
      artifact_filename TEXT NOT NULL, artifact_sha256 TEXT NOT NULL UNIQUE, artifact_size_bytes INTEGER NOT NULL,
      artifact_storage_ref TEXT NOT NULL, source_page_start INTEGER, source_page_end INTEGER, extraction_status TEXT NOT NULL,
      created_utc INTEGER NOT NULL, created_by TEXT NOT NULL);
    CREATE TABLE bug_extracted_fields(
      bug_extracted_field_id INTEGER PRIMARY KEY, bug_entry_id INTEGER NOT NULL REFERENCES bug_entries,
      bug_pdf_artifact_id INTEGER REFERENCES bug_pdf_artifacts, field_name TEXT NOT NULL, field_value_text TEXT,
      field_value_type TEXT NOT NULL, source_location_json TEXT NOT NULL, extraction_confidence REAL, created_utc INTEGER NOT NULL);
    CREATE TABLE audit_events(
      audit_event_id INTEGER PRIMARY KEY, event_type TEXT NOT NULL, entity_type TEXT NOT NULL, entity_id INTEGER NOT NULL,
      bug_entry_id INTEGER REFERENCES bug_entries, portfolio_upload_id INTEGER REFERENCES portfolio_uploads,
      event_payload_json TEXT NOT NULL, created_by TEXT NOT NULL, created_utc INTEGER NOT NULL);
    CREATE INDEX idx_bug_entries_status ON bug_entries(current_review_status_id);
    CREATE INDEX idx_mismatch_flags_type ON mismatch_flags(flag_type);
    CREATE INDEX idx_audit_events_bug_entry ON audit_events(bug_entry_id, created_utc);
    """
)
conn.execute("INSERT INTO schema_metadata VALUES (?,?)", ("schema_version", SCHEMA_VERSION))
conn.execute(
    "INSERT INTO portfolio_uploads VALUES (1,?,?,?,?,?,?,?,?,?)",
    (
        "Genti Demo Portfolio",
        "genti-demo-portfolio.pdf",
        "application/pdf",
        4194304,
        h("genti-demo-portfolio.pdf"),
        "PROCESSED",
        SYSTEM_ACTOR,
        SEED_UTC,
        SEED_UTC + 60,
    ),
)
conn.executemany(
    "INSERT INTO maintenance_packs VALUES (?,?,?,?,?,?,?,?)",
    [
        (1, None, "MP2", "Maintenance Pack 2", "MP2", 10, 1, SEED_UTC),
        (2, 1, "MP2.1", "Maintenance Pack 2.1", "MP2 / MP2.1", 20, 1, SEED_UTC),
        (3, 1, "MP2.2", "Maintenance Pack 2.2", "MP2 / MP2.2", 30, 1, SEED_UTC),
    ],
)
conn.executemany(
    "INSERT INTO review_statuses VALUES (?,?,?,?,?,?)",
    [(i, code, label, i * 10, 1, SEED_UTC) for i, code, label in STATUSES],
)
conn.executemany(
    "INSERT INTO tag_dictionary VALUES (?,?,?,?,?,?,?)",
    [(i, name, code, i * 10, 1, SYSTEM_ACTOR, SEED_UTC) for i, name, code in TAGS],
)

pdf_bugs = [
    (1, "BUG-134", "MP2 / MP2.1", "Billing", "Invoice tax rounding issue"),
    (2, "BUG-135", "MP2 / MP2.1", "Orders", "Order retry timeout"),
    (3, "BUG-136", "MP2 / MP2.1", "Inventory", "Stock sync delay"),
    (4, "BUG-137", "MP2 / MP2.2", "Payments", "Payment token refresh"),
    (5, "BUG-138", "MP2 / MP2.2", "Reporting", "Export layout adjustment"),
    (6, "BUG-139", "MP2 / MP2.2", "Security", "Session renewal behavior"),
    (7, "BUG-140", "MP2 / MP2.1", "API", "REST pagination fix"),
    (8, "BUG-141", "MP2 / MP2.1", "UI", "Inline warning placement"),
    (9, "BUG-142", "MP2 / MP2.2", "Search", "Search relevance correction"),
]
for i, bug, path, sub, title in pdf_bugs:
    conn.execute(
        "INSERT INTO portfolio_bug_inventory VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            i,
            1,
            bug,
            path,
            sub,
            title,
            f"{title} description",
            f"Validate {bug}",
            i + 9,
            i + 10,
            json.dumps({"source": "pdf", "bug": bug}, sort_keys=True),
            "EXTRACTED",
            SEED_UTC,
        ),
    )

web_bugs = [
    (1, "BUG-134", "MP2 / MP2.1", "Billing", "Invoice tax rounding issue"),
    (2, "BUG-135", "MP2 / MP2.1", "Orders", "Order retry timeout"),
    (3, "BUG-136", "MP2 / MP2.1", "Inventory", "Stock synchronization delay"),
    (4, "BUG-137", "MP2 / MP2.2", "Payment", "Payment token refresh"),
    (5, "BUG-138", "MP2 / MP2.2", "Reporting", "Export layout adjustment"),
    (6, "BUG-139", "MP2 / MP2.2", "Security", "Session renewal behavior"),
    (7, "BUG-143", "MP2 / MP2.2", "Workflow", "Approval routing correction"),
    (8, "BUG-144", "MP2 / MP2.1", "Notifications", "Notification delivery delay"),
]
for i, bug, path, sub, title in web_bugs:
    conn.execute(
        "INSERT INTO website_bug_inventory VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            i,
            "site-batch-001",
            f"https://internal.example.invalid/bugs/{bug}",
            bug,
            path,
            sub,
            title,
            f"{title} description",
            json.dumps({"source": "website", "bug": bug}, sort_keys=True),
            "IMPORTED",
            SEED_UTC,
        ),
    )

entries = [
    (1, "BUG-134", "Invoice tax rounding issue", 2, 1, 1, "MATCHED", "MEDIUM"),
    (2, "BUG-135", "Order retry timeout", 2, 2, 2, "MATCHED", "MEDIUM"),
    (3, "BUG-136", "Stock sync delay", 2, 3, 3, "FIELD_MISMATCH", "HIGH"),
    (4, "BUG-137", "Payment token refresh", 3, 4, 4, "FIELD_MISMATCH", "HIGH"),
    (5, "BUG-138", "Export layout adjustment", 3, 5, 5, "MATCHED", "LOW"),
    (6, "BUG-139", "Session renewal behavior", 3, 6, 6, "MATCHED", "HIGH"),
    (7, "BUG-140", "REST pagination fix", 2, 7, None, "PDF_ONLY", "MEDIUM"),
    (8, "BUG-141", "Inline warning placement", 2, 8, None, "PDF_ONLY", "LOW"),
    (9, "BUG-142", "Search relevance correction", 3, 9, None, "PDF_ONLY", "MEDIUM"),
    (10, "BUG-143", "Approval routing correction", 3, None, 7, "WEBSITE_ONLY", "MEDIUM"),
    (11, "BUG-144", "Notification delivery delay", 2, None, 8, "WEBSITE_ONLY", "MEDIUM"),
]
conn.executemany(
    "INSERT INTO bug_entries VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
    [
        (i, bug, title, 1, mp, pdf, web, state, priority, 1, SEED_UTC, SYSTEM_ACTOR, SEED_UTC, SYSTEM_ACTOR)
        for i, bug, title, mp, pdf, web, state, priority in entries
    ],
)
flags = [
    (1, "MATCHED", None, None, None),
    (2, "MATCHED", None, None, None),
    (3, "FIELD_MISMATCH", "title", "Stock sync delay", "Stock synchronization delay"),
    (4, "FIELD_MISMATCH", "subsystem", "Payments", "Payment"),
    (5, "MATCHED", None, None, None),
    (6, "MATCHED", None, None, None),
    (7, "PDF_ONLY", None, "REST pagination fix", None),
    (8, "PDF_ONLY", None, "Inline warning placement", None),
    (9, "PDF_ONLY", None, "Search relevance correction", None),
    (10, "WEBSITE_ONLY", None, None, "Approval routing correction"),
    (11, "WEBSITE_ONLY", None, None, "Notification delivery delay"),
]
conn.executemany(
    "INSERT INTO mismatch_flags VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
    [
        (i, i, typ, field, pdf, web, "WARN" if typ != "MATCHED" else "INFO", 1, "OPEN", None, None, SEED_UTC)
        for i, typ, field, pdf, web in flags
    ],
)
for aid, bid, pdfid, name in [
    (1, 1, 1, "BUG-134__demo.pdf"),
    (2, 3, 3, "BUG-136__demo.pdf"),
    (3, 7, 7, "BUG-140__demo.pdf"),
]:
    conn.execute(
        "INSERT INTO bug_pdf_artifacts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (aid, bid, 1, pdfid, name, h(name), 65536 + aid, f"dbblob://bug_pdf_artifacts/{aid}", 10 + aid, 11 + aid, "EXTRACTED", SEED_UTC, SYSTEM_ACTOR),
    )
fields = [
    (1, 1, 1, "Subsystem", "Billing"),
    (2, 1, 1, "Title", "Invoice tax rounding issue"),
    (3, 1, 1, "Description", "Tax rounding differs after MP2.1 upgrade"),
    (4, 1, 1, "Steps", "Validate invoice totals"),
    (5, 1, 1, "Screenshots", "screenshot_ref:BUG-134"),
    (6, 3, 2, "Subsystem", "Inventory"),
    (7, 3, 2, "Title", "Stock sync delay"),
    (8, 3, 2, "Description", "Inventory sync may lag"),
    (9, 3, 2, "Steps", "Compare sync timestamps"),
    (10, 7, 3, "Title", "REST pagination fix"),
]
conn.executemany(
    "INSERT INTO bug_extracted_fields VALUES (?,?,?,?,?,?,?,?,?)",
    [
        (i, bid, pdfid, field, value, "IMAGE" if field == "Screenshots" else "TEXT", json.dumps({"source": "seed"}), 1.0, SEED_UTC)
        for i, bid, pdfid, field, value in fields
    ],
)
conn.execute(
    "INSERT INTO bug_entry_notes VALUES (1,3,'Initial seed note: confirm mismatch with functional owner.','REVIEW',?,?,0)",
    (SYSTEM_ACTOR, SEED_UTC),
)
for bug_entry_id in [1, 3, 7]:
    conn.execute(
        "INSERT INTO audit_events VALUES (?,?,?,?,?,?,?,?,?)",
        (bug_entry_id, "BUG_ENTRY_CREATED", "bug_entries", bug_entry_id, bug_entry_id, 1, json.dumps({"source": "seed"}), SYSTEM_ACTOR, SEED_UTC),
    )

bug_entry_id = 3
action_utc = SEED_UTC + 600
from_status = conn.execute("SELECT current_review_status_id FROM bug_entries WHERE bug_entry_id=?", (bug_entry_id,)).fetchone()[0]
to_status = conn.execute("SELECT review_status_id FROM review_statuses WHERE status_code='TEST_REQUIRED'").fetchone()[0]
conn.execute(
    "INSERT INTO bug_entry_status_history VALUES (1,?,?,?,?,?,?,?)",
    (bug_entry_id, from_status, to_status, "demo_validation", "Needs validation against MP2.1 test environment before confirmation.", REVIEWER_ACTOR, action_utc),
)
conn.execute(
    "UPDATE bug_entries SET current_review_status_id=?, updated_utc=?, updated_by=? WHERE bug_entry_id=?",
    (to_status, action_utc, REVIEWER_ACTOR, bug_entry_id),
)
conn.execute("INSERT INTO bug_entry_tags VALUES (1,?,?,?, ?, NULL, NULL)", (bug_entry_id, 1, REVIEWER_ACTOR, action_utc + 1))
conn.execute(
    "INSERT INTO bug_entry_notes VALUES (2,?,'Needs validation against MP2.1 test environment before confirmation.','REVIEW',?,?,0)",
    (bug_entry_id, REVIEWER_ACTOR, action_utc + 2),
)
for aid, event, entity, entity_id, payload in [
    (100, "STATUS_CHANGED", "bug_entries", bug_entry_id, {"from_status_id": from_status, "to_status_id": to_status}),
    (101, "TAG_APPLIED", "bug_entry_tags", 1, {"tag_id": 1}),
    (102, "NOTE_CREATED", "bug_entry_notes", 2, {"note_id": 2}),
]:
    conn.execute(
        "INSERT INTO audit_events VALUES (?,?,?,?,?,?,?,?,?)",
        (aid, event, entity, entity_id, bug_entry_id, 1, json.dumps(payload, sort_keys=True), REVIEWER_ACTOR, action_utc + aid),
    )
conn.commit()

failures = []
def require(condition, message):
    if not condition:
        failures.append(message)

require(count(conn, "SELECT COUNT(*) FROM portfolio_uploads") >= 1, "missing portfolio upload")
require(count(conn, "SELECT COUNT(*) FROM bug_entries") >= 8, "expected at least eight bug entries")
for _, code, _ in STATUSES:
    require(count(conn, "SELECT COUNT(*) FROM review_statuses WHERE status_code=?", (code,)) == 1, f"missing status {code}")
for _, _, code in TAGS:
    require(count(conn, "SELECT COUNT(*) FROM tag_dictionary WHERE tag_code=?", (code,)) == 1, f"missing tag {code}")
for flag_type in ["PDF_ONLY", "WEBSITE_ONLY", "FIELD_MISMATCH"]:
    require(count(conn, "SELECT COUNT(*) FROM mismatch_flags WHERE flag_type=?", (flag_type,)) >= 1, f"missing {flag_type}")
require(count(conn, "SELECT COUNT(DISTINCT bug_entry_id) FROM bug_extracted_fields") >= 1, "missing extracted fields")
require(count(conn, "SELECT COUNT(DISTINCT bug_entry_id) FROM bug_pdf_artifacts") >= 1, "missing Bug PDF artifact reference")
require(count(conn, "SELECT COUNT(*) FROM bug_entry_status_history") >= 1, "missing status history")
require(count(conn, "SELECT COUNT(*) FROM bug_entry_tags WHERE removed_utc IS NULL") >= 1, "missing active tag assignment")
require(count(conn, "SELECT COUNT(*) FROM bug_entry_notes WHERE is_deleted=0") >= 2, "missing manual notes")
for event_type in ["STATUS_CHANGED", "TAG_APPLIED", "NOTE_CREATED"]:
    require(count(conn, "SELECT COUNT(*) FROM audit_events WHERE event_type=?", (event_type,)) >= 1, f"missing audit event {event_type}")
if failures:
    raise SystemExit("Gate 21Q validation failed:\n- " + "\n- ".join(failures))

summary = {
    "schema_version": conn.execute("SELECT schema_value FROM schema_metadata WHERE schema_key='schema_version'").fetchone()[0],
    "portfolio_uploads": count(conn, "SELECT COUNT(*) FROM portfolio_uploads"),
    "maintenance_packs": count(conn, "SELECT COUNT(*) FROM maintenance_packs"),
    "bug_entries": count(conn, "SELECT COUNT(*) FROM bug_entries"),
    "mismatch_flags": count(conn, "SELECT COUNT(*) FROM mismatch_flags"),
    "pdf_only_mismatches": count(conn, "SELECT COUNT(*) FROM mismatch_flags WHERE flag_type='PDF_ONLY'"),
    "website_only_mismatches": count(conn, "SELECT COUNT(*) FROM mismatch_flags WHERE flag_type='WEBSITE_ONLY'"),
    "field_mismatches": count(conn, "SELECT COUNT(*) FROM mismatch_flags WHERE flag_type='FIELD_MISMATCH'"),
    "review_statuses": count(conn, "SELECT COUNT(*) FROM review_statuses"),
    "tags": count(conn, "SELECT COUNT(*) FROM tag_dictionary"),
    "status_history_rows": count(conn, "SELECT COUNT(*) FROM bug_entry_status_history"),
    "tag_assignment_rows": count(conn, "SELECT COUNT(*) FROM bug_entry_tags WHERE removed_utc IS NULL"),
    "note_rows": count(conn, "SELECT COUNT(*) FROM bug_entry_notes WHERE is_deleted=0"),
    "bug_pdf_artifacts": count(conn, "SELECT COUNT(*) FROM bug_pdf_artifacts"),
    "bug_extracted_fields": count(conn, "SELECT COUNT(*) FROM bug_extracted_fields"),
    "audit_events": count(conn, "SELECT COUNT(*) FROM audit_events"),
}
print("Gate 21Q seeded schema validation passed")
for key in sorted(summary):
    print(f"{key}: {summary[key]}")
conn.close()
PY
