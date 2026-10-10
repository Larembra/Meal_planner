"""Заменяет недоступные ссылки изображений на рабочие уникальные ссылки."""

from alembic import op

revision = "20261016_working_recipe_images"
down_revision = "20261015_unique_recipe_images"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        WITH numbered AS (
            SELECT id, row_number() OVER (ORDER BY id) AS image_number
            FROM meals
        )
        UPDATE meals AS meal
        SET image_url = 'https://picsum.photos/seed/meal-'
                       || numbered.image_number || '/1200/800'
        FROM numbered
        WHERE meal.id = numbered.id
        """
    )


def downgrade():
    """Оставляет рабочие изображения при откате миграции."""
