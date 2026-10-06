"""Начальная ERD-схема приложения."""
from alembic import op
from app.db.base import Base
from app.models import models

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    Base.metadata.create_all(op.get_bind())


def downgrade():
    Base.metadata.drop_all(op.get_bind())
