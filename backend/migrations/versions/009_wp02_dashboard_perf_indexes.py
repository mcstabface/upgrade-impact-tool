from alembic import op


revision = "009_wp02_dashboard_perf"
down_revision = "008_notification_delivery"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_analysis_applications_analysis_id",
        "analysis_applications",
        ["analysis_id"],
    )

    op.create_index(
        "ix_analysis_runs_completed_utc",
        "analysis_runs",
        ["completed_utc"],
    )

    op.create_index(
        "ix_analysis_findings_status_severity_headline",
        "analysis_findings",
        ["finding_status", "severity", "headline"],
    )

    op.create_index(
        "ix_analysis_findings_status_severity_recommended_action",
        "analysis_findings",
        ["finding_status", "severity", "recommended_action"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_analysis_findings_status_severity_recommended_action",
        table_name="analysis_findings",
    )
    op.drop_index(
        "ix_analysis_findings_status_severity_headline",
        table_name="analysis_findings",
    )
    op.drop_index(
        "ix_analysis_runs_completed_utc",
        table_name="analysis_runs",
    )
    op.drop_index(
        "ix_analysis_applications_analysis_id",
        table_name="analysis_applications",
    )