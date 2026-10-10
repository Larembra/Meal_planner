"""Добавляет итоговую стоимость объединенной позиции списка покупок."""

from alembic import op
import sqlalchemy as sa

revision = "20261011_shop_total_cost"
down_revision = "20261009_second_breakfast"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("shopping_items")}
    if "total_cost" not in columns:
        op.add_column(
            "shopping_items",
            sa.Column("total_cost", sa.Numeric(10, 2), nullable=False, server_default="0"),
        )
        op.execute(
            """
            UPDATE shopping_items AS item
            SET total_cost = products.cost
            FROM products
            WHERE products.id = item.product_id
            """
        )


def downgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("shopping_items")}
    if "total_cost" in columns:
        op.drop_column("shopping_items", "total_cost")
