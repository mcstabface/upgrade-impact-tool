from alembic import op
import sqlalchemy as sa


revision = "004_review_item_transitions"
down_revision = "003_review_items"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("review_items", sa.Column("resolution_note", sa.Text(), nullable=True))
    op.add_column("review_items", sa.Column("defer_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("review_items", "defer_reason")
    op.drop_column("review_items", "resolution_note")