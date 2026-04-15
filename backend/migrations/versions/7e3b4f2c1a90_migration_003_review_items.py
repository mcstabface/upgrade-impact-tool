from alembic import op
import sqlalchemy as sa


revision = "003_review_items"
down_revision = "002_intake_drafts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "review_items",
        sa.Column("review_item_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("finding_id", sa.BigInteger(), sa.ForeignKey("analysis_findings.finding_id"), nullable=False),
        sa.Column("analysis_id", sa.Text(), nullable=False),
        sa.Column("application_name", sa.Text(), nullable=False),
        sa.Column("finding_headline", sa.Text(), nullable=False),
        sa.Column("kb_reference", sa.Text(), nullable=False),
        sa.Column("review_reason", sa.Text(), nullable=False),
        sa.Column("assigned_owner_user_id", sa.Text(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("review_status", sa.Text(), nullable=False, server_default="OPEN"),
        sa.Column("created_utc", sa.BigInteger(), nullable=False),
        sa.Column("updated_utc", sa.BigInteger(), nullable=False),
        sa.Column("created_by_user_id", sa.Text(), nullable=False),
    )

    op.create_index(
        "ix_review_items_finding_id",
        "review_items",
        ["finding_id"],
    )

    op.create_index(
        "ix_review_items_status_due_date",
        "review_items",
        ["review_status", "due_date"],
    )

    op.create_index(
        "ix_review_items_owner_status",
        "review_items",
        ["assigned_owner_user_id", "review_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_review_items_owner_status", table_name="review_items")
    op.drop_index("ix_review_items_status_due_date", table_name="review_items")
    op.drop_index("ix_review_items_finding_id", table_name="review_items")
    op.drop_table("review_items")