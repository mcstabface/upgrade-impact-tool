from alembic import op


revision = "012_wp02_drop_dup_prev_idx"
down_revision = "011_wp02_delta_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index(
        "ix_ar_prev_analysis_id",
        table_name="analysis_runs",
    )


def downgrade() -> None:
    op.create_index(
        "ix_ar_prev_analysis_id",
        "analysis_runs",
        ["previous_analysis_id"],
    )