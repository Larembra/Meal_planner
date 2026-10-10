"""Убирает ошибочный default у необязательной связи списка покупок с рационом."""

from alembic import op

revision = "20261012_shopping_ration_default"
down_revision = "20261011_shop_total_cost"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("shopping_lists", "ration_id", server_default=None)


def downgrade():
    """Откат не восстанавливает ошибочный default."""
