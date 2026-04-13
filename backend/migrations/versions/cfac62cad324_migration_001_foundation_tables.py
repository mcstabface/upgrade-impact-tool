from alembic import op
import sqlalchemy as sa


revision = "001_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("customer_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("customer_name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="ACTIVE"),
        sa.Column("created_utc", sa.BigInteger(), nullable=False),
        sa.Column("updated_utc", sa.BigInteger(), nullable=False),
    )

    op.create_table(
        "environments",
        sa.Column("environment_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("customer_id", sa.BigInteger(), sa.ForeignKey("customers.customer_id"), nullable=False),
        sa.Column("environment_name", sa.Text(), nullable=False),
        sa.Column("environment_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="ACTIVE"),
        sa.Column("created_utc", sa.BigInteger(), nullable=False),
        sa.Column("updated_utc", sa.BigInteger(), nullable=False),
    )

    op.create_table(
        "customer_state_snapshots",
        sa.Column("snapshot_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("customer_id", sa.BigInteger(), sa.ForeignKey("customers.customer_id"), nullable=False),
        sa.Column("environment_id", sa.BigInteger(), sa.ForeignKey("environments.environment_id"), nullable=False),
        sa.Column("snapshot_version", sa.Integer(), nullable=False),
        sa.Column("snapshot_status", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("completeness_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_utc", sa.BigInteger(), nullable=False),
        sa.Column("created_by_user_id", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.create_table(
        "customer_applications",
        sa.Column("customer_application_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("snapshot_id", sa.BigInteger(), sa.ForeignKey("customer_state_snapshots.snapshot_id"), nullable=False),
        sa.Column("application_name", sa.Text(), nullable=False),
        sa.Column("product_line", sa.Text(), nullable=False),
        sa.Column("current_version", sa.Text(), nullable=False),
        sa.Column("target_version", sa.Text(), nullable=False),
        sa.Column("application_status", sa.Text(), nullable=False),
    )

    op.create_table(
        "customer_modules",
        sa.Column("customer_module_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("customer_application_id", sa.BigInteger(), sa.ForeignKey("customer_applications.customer_application_id"), nullable=False),
        sa.Column("module_name", sa.Text(), nullable=False),
    )

    op.create_table(
        "kb_articles",
        sa.Column("kb_article_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("kb_article_number", sa.Text(), nullable=False),
        sa.Column("kb_title", sa.Text(), nullable=False),
        sa.Column("kb_url", sa.Text(), nullable=False),
        sa.Column("product_line", sa.Text(), nullable=False),
        sa.Column("application_name", sa.Text(), nullable=False),
        sa.Column("published_date", sa.Text(), nullable=False),
        sa.Column("current_status", sa.Text(), nullable=False),
        sa.Column("created_utc", sa.BigInteger(), nullable=False),
        sa.Column("updated_utc", sa.BigInteger(), nullable=False),
    )

    op.create_table(
        "kb_article_versions",
        sa.Column("kb_article_version_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("kb_article_id", sa.BigInteger(), sa.ForeignKey("kb_articles.kb_article_id"), nullable=False),
        sa.Column("source_hash", sa.Text(), nullable=False),
        sa.Column("ingestion_run_id", sa.Text(), nullable=True),
        sa.Column("parsed_status", sa.Text(), nullable=False),
        sa.Column("normalization_status", sa.Text(), nullable=False),
        sa.Column("extracted_utc", sa.BigInteger(), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.create_table(
        "change_records",
        sa.Column("change_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("schema_version", sa.Text(), nullable=False),
        sa.Column("kb_article_id", sa.BigInteger(), sa.ForeignKey("kb_articles.kb_article_id"), nullable=False),
        sa.Column("kb_article_version_id", sa.BigInteger(), sa.ForeignKey("kb_article_versions.kb_article_version_id"), nullable=False),
        sa.Column("product_line", sa.Text(), nullable=False),
        sa.Column("application_name", sa.Text(), nullable=False),
        sa.Column("module_name", sa.Text(), nullable=True),
        sa.Column("functional_area", sa.Text(), nullable=True),
        sa.Column("version_from", sa.Text(), nullable=True),
        sa.Column("version_to", sa.Text(), nullable=True),
        sa.Column("change_taxonomy", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("impact_type", sa.Text(), nullable=False),
        sa.Column("headline", sa.Text(), nullable=False),
        sa.Column("plain_language_summary", sa.Text(), nullable=False),
        sa.Column("business_impact_summary", sa.Text(), nullable=True),
        sa.Column("technical_impact_summary", sa.Text(), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("user_confidence_note", sa.Text(), nullable=True),
        sa.Column("standard_usage_assumed", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("customization_review_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("integration_review_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("extraction_status", sa.Text(), nullable=False),
        sa.Column("normalization_status", sa.Text(), nullable=False),
        sa.Column("review_status", sa.Text(), nullable=False),
        sa.Column("created_utc", sa.BigInteger(), nullable=False),
        sa.Column("updated_utc", sa.BigInteger(), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=False),
    )

    op.create_table(
        "analysis_runs",
        sa.Column("analysis_id", sa.Text(), primary_key=True),
        sa.Column("customer_id", sa.BigInteger(), sa.ForeignKey("customers.customer_id"), nullable=False),
        sa.Column("environment_id", sa.BigInteger(), sa.ForeignKey("environments.environment_id"), nullable=False),
        sa.Column("snapshot_id", sa.BigInteger(), sa.ForeignKey("customer_state_snapshots.snapshot_id"), nullable=False),
        sa.Column("kb_catalog_version", sa.Text(), nullable=True),
        sa.Column("analysis_status", sa.Text(), nullable=False),
        sa.Column("overall_status", sa.Text(), nullable=False),
        sa.Column("applies_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("review_required_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unknown_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("blocked_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("assumptions_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("missing_inputs_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("derived_risks_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_utc", sa.BigInteger(), nullable=True),
        sa.Column("completed_utc", sa.BigInteger(), nullable=True),
        sa.Column("duration_ms", sa.BigInteger(), nullable=True),
        sa.Column("created_by_user_id", sa.Text(), nullable=True),
    )

    op.create_table(
        "analysis_applications",
        sa.Column("analysis_application_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("analysis_id", sa.Text(), sa.ForeignKey("analysis_runs.analysis_id"), nullable=False),
        sa.Column("application_name", sa.Text(), nullable=False),
        sa.Column("current_version", sa.Text(), nullable=False),
        sa.Column("target_version", sa.Text(), nullable=False),
        sa.Column("application_status", sa.Text(), nullable=False),
        sa.Column("findings_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("review_required_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("blocked_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unknown_count", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "analysis_findings",
        sa.Column("finding_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("analysis_id", sa.Text(), sa.ForeignKey("analysis_runs.analysis_id"), nullable=False),
        sa.Column("analysis_application_id", sa.BigInteger(), sa.ForeignKey("analysis_applications.analysis_application_id"), nullable=False),
        sa.Column("change_id", sa.BigInteger(), sa.ForeignKey("change_records.change_id"), nullable=False),
        sa.Column("finding_status", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("change_taxonomy", sa.Text(), nullable=False),
        sa.Column("impact_type", sa.Text(), nullable=False),
        sa.Column("headline", sa.Text(), nullable=False),
        sa.Column("plain_language_summary", sa.Text(), nullable=False),
        sa.Column("business_impact_summary", sa.Text(), nullable=True),
        sa.Column("technical_impact_summary", sa.Text(), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("reason_for_status", sa.Text(), nullable=True),
        sa.Column("assumptions_text", sa.Text(), nullable=True),
        sa.Column("missing_inputs_text", sa.Text(), nullable=True),
        sa.Column("requires_review", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_blocking", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_utc", sa.BigInteger(), nullable=False),
    )

    op.create_table(
        "finding_evidence",
        sa.Column("finding_evidence_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("finding_id", sa.BigInteger(), sa.ForeignKey("analysis_findings.finding_id"), nullable=False),
        sa.Column("kb_article_number", sa.Text(), nullable=False),
        sa.Column("kb_title", sa.Text(), nullable=False),
        sa.Column("kb_url", sa.Text(), nullable=False),
        sa.Column("publication_date", sa.Text(), nullable=False),
        sa.Column("evidence_excerpt", sa.Text(), nullable=False),
        sa.Column("reference_section", sa.Text(), nullable=True),
    )

    op.create_table(
        "state_transitions",
        sa.Column("state_transition_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("analysis_id", sa.Text(), sa.ForeignKey("analysis_runs.analysis_id"), nullable=False),
        sa.Column("previous_state", sa.Text(), nullable=True),
        sa.Column("new_state", sa.Text(), nullable=False),
        sa.Column("trigger_event", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=True),
        sa.Column("transition_utc", sa.BigInteger(), nullable=False),
    )

    op.create_index("ix_kb_articles_kb_article_number", "kb_articles", ["kb_article_number"], unique=True)
    op.create_index("ix_kb_articles_application_name_published_date", "kb_articles", ["application_name", "published_date"])
    op.create_index("ix_kb_article_versions_kb_article_id_is_current", "kb_article_versions", ["kb_article_id", "is_current"])
    op.create_index("ix_kb_article_versions_source_hash", "kb_article_versions", ["source_hash"])
    op.create_index("ix_customer_state_snapshots_customer_env_active", "customer_state_snapshots", ["customer_id", "environment_id", "is_active"])
    op.create_index("ix_customer_state_snapshots_content_hash", "customer_state_snapshots", ["content_hash"])
    op.create_index("ix_customer_applications_snapshot_app_name", "customer_applications", ["snapshot_id", "application_name"])
    op.create_index("ix_change_records_app_module_versions", "change_records", ["application_name", "module_name", "version_from", "version_to"])
    op.create_index("ix_change_records_change_taxonomy", "change_records", ["change_taxonomy"])
    op.create_index("ix_change_records_severity", "change_records", ["severity"])
    op.create_index("ix_change_records_kb_article_id", "change_records", ["kb_article_id"])
    op.create_index("ix_analysis_runs_customer_env_completed", "analysis_runs", ["customer_id", "environment_id", "completed_utc"])
    op.create_index("ix_analysis_runs_snapshot_id", "analysis_runs", ["snapshot_id"])
    op.create_index("ix_analysis_runs_overall_status", "analysis_runs", ["overall_status"])
    op.create_index("ix_analysis_findings_analysis_id_finding_status", "analysis_findings", ["analysis_id", "finding_status"])
    op.create_index("ix_analysis_findings_analysis_app_severity", "analysis_findings", ["analysis_application_id", "severity"])
    op.create_index("ix_analysis_findings_change_id", "analysis_findings", ["change_id"])
    op.create_index("ix_analysis_findings_requires_review_is_blocking", "analysis_findings", ["requires_review", "is_blocking"])


def downgrade() -> None:
    op.drop_index("ix_analysis_findings_requires_review_is_blocking", table_name="analysis_findings")
    op.drop_index("ix_analysis_findings_change_id", table_name="analysis_findings")
    op.drop_index("ix_analysis_findings_analysis_app_severity", table_name="analysis_findings")
    op.drop_index("ix_analysis_findings_analysis_id_finding_status", table_name="analysis_findings")
    op.drop_index("ix_analysis_runs_overall_status", table_name="analysis_runs")
    op.drop_index("ix_analysis_runs_snapshot_id", table_name="analysis_runs")
    op.drop_index("ix_analysis_runs_customer_env_completed", table_name="analysis_runs")
    op.drop_index("ix_change_records_kb_article_id", table_name="change_records")
    op.drop_index("ix_change_records_severity", table_name="change_records")
    op.drop_index("ix_change_records_change_taxonomy", table_name="change_records")
    op.drop_index("ix_change_records_app_module_versions", table_name="change_records")
    op.drop_index("ix_customer_applications_snapshot_app_name", table_name="customer_applications")
    op.drop_index("ix_customer_state_snapshots_content_hash", table_name="customer_state_snapshots")
    op.drop_index("ix_customer_state_snapshots_customer_env_active", table_name="customer_state_snapshots")
    op.drop_index("ix_kb_article_versions_source_hash", table_name="kb_article_versions")
    op.drop_index("ix_kb_article_versions_kb_article_id_is_current", table_name="kb_article_versions")
    op.drop_index("ix_kb_articles_application_name_published_date", table_name="kb_articles")
    op.drop_index("ix_kb_articles_kb_article_number", table_name="kb_articles")

    op.drop_table("state_transitions")
    op.drop_table("finding_evidence")
    op.drop_table("analysis_findings")
    op.drop_table("analysis_applications")
    op.drop_table("analysis_runs")
    op.drop_table("change_records")
    op.drop_table("kb_article_versions")
    op.drop_table("kb_articles")
    op.drop_table("customer_modules")
    op.drop_table("customer_applications")
    op.drop_table("customer_state_snapshots")
    op.drop_table("environments")
    op.drop_table("customers")