"""Назначает каждому блюду отдельную ссылку на фотографию."""

from alembic import op

revision = "20261015_unique_recipe_images"
down_revision = "20261014_more_recipes"
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
        SET image_url = 'https://loremflickr.com/1200/800/food?lock='
                       || numbered.image_number
        FROM numbered
        WHERE meal.id = numbered.id
        """
    )


def downgrade():
    """Оставляет ранее назначенные изображения, чтобы каталог не терял фотографии."""
