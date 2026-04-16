from alembic import op
import sqlalchemy as sa


revision = "008_notification_delivery"
down_revision = "007_phase4_stale"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_deliveries",
        sa.Column("notification_id", sa.Text(), primary_key=True),
        sa.Column("notification_type", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("headline", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("target_path", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_utc", sa.BigInteger(), nullable=False),
        sa.Column("updated_utc", sa.BigInteger(), nullable=False),
    )

    op.create_index(
        "ix_notification_deliveries_active_updated",
        "notification_deliveries",
        ["is_active", "updated_utc"],
    )

    op.create_index(
        "ix_notification_deliveries_type_active",
        "notification_deliveries",
        ["notification_type", "is_active"],
    )


def downgrade() -> None:
    op.drop_index("ix_notification_deliveries_type_active", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_active_updated", table_name="notification_deliveries")
    op.drop_table("notification_deliveries")