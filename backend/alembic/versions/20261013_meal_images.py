"""Добавляет URL изображения блюда."""

from alembic import op
import sqlalchemy as sa

revision = "20261013_meal_images"
down_revision = "20261012_shopping_ration_default"
branch_labels = None
depends_on = None


def upgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("meals")}
    if "image_url" not in columns:
        op.add_column("meals", sa.Column("image_url", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("meals", "image_url")
