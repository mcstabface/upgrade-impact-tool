from alembic import op


revision = "010_wp02_analysis_detail"
down_revision = "009_wp02_dashboard_perf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_finding_evidence_finding_id",
        "finding_evidence",
        ["finding_id"],
    )

    op.create_index(
        "ix_analysis_findings_analysis_id_status_severity_headline",
        "analysis_findings",
        ["analysis_id", "finding_status", "severity", "headline"],
    )

    op.create_index(
        "ix_analysis_findings_analysis_id_status_severity_recommended_action",
        "analysis_findings",
        ["analysis_id", "finding_status", "severity", "recommended_action"],
    )

    op.create_index(
        "ix_analysis_findings_analysis_application_id_finding_id",
        "analysis_findings",
        ["analysis_application_id", "finding_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_analysis_findings_analysis_application_id_finding_id",
        table_name="analysis_findings",
    )
    op.drop_index(
        "ix_analysis_findings_analysis_id_status_severity_recommended_action",
        table_name="analysis_findings",
    )
    op.drop_index(
        "ix_analysis_findings_analysis_id_status_severity_headline",
        table_name="analysis_findings",
    )
    op.drop_index(
        "ix_finding_evidence_finding_id",
        table_name="finding_evidence",
    )