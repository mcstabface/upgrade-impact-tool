from alembic import op
import sqlalchemy as sa


revision = "005_review_item_assignment_updates"
down_revision = "004_review_item_transitions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("review_items", sa.Column("assignment_updated_utc", sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("review_items", "assignment_updated_utc")