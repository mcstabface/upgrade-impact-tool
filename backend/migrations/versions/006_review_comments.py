from alembic import op
import sqlalchemy as sa


revision = "006_review_comments"
down_revision = "005_review_item_assign"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "review_comments",
        sa.Column("comment_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("review_item_id", sa.BigInteger(), sa.ForeignKey("review_items.review_item_id"), nullable=False),
        sa.Column("comment_text", sa.Text(), nullable=False),
        sa.Column("created_by_user_id", sa.Text(), nullable=False),
        sa.Column("created_utc", sa.BigInteger(), nullable=False),
    )

    op.create_index(
        "ix_review_comments_review_item_created_utc",
        "review_comments",
        ["review_item_id", "created_utc"],
    )


def downgrade() -> None:
    op.drop_index("ix_review_comments_review_item_created_utc", table_name="review_comments")
    op.drop_table("review_comments")