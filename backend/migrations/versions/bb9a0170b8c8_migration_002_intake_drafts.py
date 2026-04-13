from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "002_intake_drafts"
down_revision = "001_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "intake_drafts",
        sa.Column("intake_id", sa.Text(), primary_key=True),
        sa.Column("customer_name", sa.Text(), nullable=False),
        sa.Column("environment_name", sa.Text(), nullable=False),
        sa.Column("environment_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("completeness_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_utc", sa.BigInteger(), nullable=False),
        sa.Column("updated_utc", sa.BigInteger(), nullable=False),
    )

    op.create_index(
        "ix_intake_drafts_status_updated_utc",
        "intake_drafts",
        ["status", "updated_utc"],
    )


def downgrade() -> None:
    op.drop_index("ix_intake_drafts_status_updated_utc", table_name="intake_drafts")
    op.drop_table("intake_drafts")