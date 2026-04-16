from alembic import op


revision = "011_wp02_delta_audit"
down_revision = "010_wp02_analysis_detail"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_ar_prev_analysis_id",
        "analysis_runs",
        ["previous_analysis_id"],
    )

    op.create_index(
        "ix_st_analysis_id_transition_utc",
        "state_transitions",
        ["analysis_id", "transition_utc"],
    )

    op.create_index(
        "ix_af_analysis_id_change_id",
        "analysis_findings",
        ["analysis_id", "change_id"],
    )

    op.create_index(
        "ix_af_analysis_id_app_id",
        "analysis_findings",
        ["analysis_id", "analysis_application_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_af_analysis_id_app_id",
        table_name="analysis_findings",
    )
    op.drop_index(
        "ix_af_analysis_id_change_id",
        table_name="analysis_findings",
    )
    op.drop_index(
        "ix_st_analysis_id_transition_utc",
        table_name="state_transitions",
    )
    op.drop_index(
        "ix_ar_prev_analysis_id",
        table_name="analysis_runs",
    )