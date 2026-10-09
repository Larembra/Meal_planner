"""Allow a separate second-breakfast ration slot.

Revision ID: 20261009_second_breakfast
Revises: None
"""
from alembic import op

revision = "20261009_second_breakfast"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ration_meals_type_check", "ration_meals", type_="check")
    op.create_check_constraint(
        "ration_meals_type_check",
        "ration_meals",
        "meal_type IN ('breakfast', 'second_breakfast', 'lunch', 'dinner', 'snack')",
    )


def downgrade() -> None:
    op.drop_constraint("ration_meals_type_check", "ration_meals", type_="check")
    op.create_check_constraint(
        "ration_meals_type_check",
        "ration_meals",
        "meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')",
    )
