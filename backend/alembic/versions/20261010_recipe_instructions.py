"""Добавляет отдельные инструкции приготовления к блюдам."""

from alembic import op
import sqlalchemy as sa

revision = "20261010_recipe_instructions"
down_revision = "20261009_second_breakfast"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("meals")}
    if "instructions" not in columns:
        op.add_column("meals", sa.Column("instructions", sa.Text(), nullable=False, server_default=""))


def downgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("meals")}
    if "instructions" in columns:
        op.drop_column("meals", "instructions")
