from alembic import op


revision = "010_wp02_analysis_detail"
down_revision = "009_wp02_dashboard_perf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_fe_finding_id",
        "finding_evidence",
        ["finding_id"],
    )

    op.create_index(
        "ix_af_aid_status_sev_headline",
        "analysis_findings",
        ["analysis_id", "finding_status", "severity", "headline"],
    )

    op.create_index(
        "ix_af_aid_status_sev_action",
        "analysis_findings",
        ["analysis_id", "finding_status", "severity", "recommended_action"],
    )

    op.create_index(
        "ix_af_app_id_finding_id",
        "analysis_findings",
        ["analysis_application_id", "finding_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_af_app_id_finding_id",
        table_name="analysis_findings",
    )
    op.drop_index(
        "ix_af_aid_status_sev_action",
        table_name="analysis_findings",
    )
    op.drop_index(
        "ix_af_aid_status_sev_headline",
        table_name="analysis_findings",
    )
    op.drop_index(
        "ix_fe_finding_id",
        table_name="finding_evidence",
    )