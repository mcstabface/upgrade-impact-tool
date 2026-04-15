from alembic import op
import sqlalchemy as sa


revision = "007_phase4_stale"
down_revision = "006_review_comments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "analysis_runs",
        sa.Column("previous_analysis_id", sa.Text(), nullable=True),
    )
    op.add_column(
        "analysis_runs",
        sa.Column("snapshot_hash", sa.Text(), nullable=True),
    )
    op.add_column(
        "analysis_runs",
        sa.Column("analysis_input_hash", sa.Text(), nullable=True),
    )
    op.add_column(
        "analysis_runs",
        sa.Column("stale_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "analysis_runs",
        sa.Column("stale_detected_utc", sa.BigInteger(), nullable=True),
    )

    op.execute(
        """
        WITH kb_state AS (
            SELECT
                COALESCE(
                    md5(
                        COALESCE(
                            string_agg(
                                ka.kb_article_number || ':' || kav.content_hash,
                                '|' ORDER BY ka.kb_article_number, kav.kb_article_version_id
                            ),
                            ''
                        )
                    ),
                    md5('')
                ) AS kb_catalog_hash
            FROM kb_article_versions kav
            JOIN kb_articles ka ON ka.kb_article_id = kav.kb_article_id
            WHERE kav.is_current = true
        )
        UPDATE analysis_runs ar
        SET
            snapshot_hash = css.content_hash,
            kb_catalog_version = kb_state.kb_catalog_hash,
            analysis_input_hash = md5(css.content_hash || '|' || kb_state.kb_catalog_hash)
        FROM customer_state_snapshots css, kb_state
        WHERE css.snapshot_id = ar.snapshot_id
        """
    )

    op.create_index(
        "ix_analysis_runs_previous_analysis_id",
        "analysis_runs",
        ["previous_analysis_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_analysis_runs_previous_analysis_id", table_name="analysis_runs")
    op.drop_column("analysis_runs", "stale_detected_utc")
    op.drop_column("analysis_runs", "stale_reason")
    op.drop_column("analysis_runs", "analysis_input_hash")
    op.drop_column("analysis_runs", "snapshot_hash")
    op.drop_column("analysis_runs", "previous_analysis_id")