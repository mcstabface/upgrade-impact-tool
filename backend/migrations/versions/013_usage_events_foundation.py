from alembic import op
import sqlalchemy as sa


revision = "013_usage_events_found"
down_revision = "012_wp02_drop_dup_prev_idx"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usage_events",
        sa.Column("usage_event_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("actor_role", sa.Text(), nullable=False),
        sa.Column("actor_user_id", sa.Text(), nullable=True),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", sa.Text(), nullable=False),
        sa.Column("related_analysis_id", sa.Text(), nullable=True),
        sa.Column("event_payload", sa.JSON(), nullable=True),
        sa.Column("created_utc", sa.BigInteger(), nullable=False),
    )

    op.create_index(
        "ix_usage_events_event_type_created_utc",
        "usage_events",
        ["event_type", "created_utc"],
    )

    op.create_index(
        "ix_usage_events_entity_type_entity_id",
        "usage_events",
        ["entity_type", "entity_id"],
    )

    op.create_index(
        "ix_usage_events_related_analysis_id",
        "usage_events",
        ["related_analysis_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_usage_events_related_analysis_id",
        table_name="usage_events",
    )
    op.drop_index(
        "ix_usage_events_entity_type_entity_id",
        table_name="usage_events",
    )
    op.drop_index(
        "ix_usage_events_event_type_created_utc",
        table_name="usage_events",
    )
    op.drop_table("usage_events")