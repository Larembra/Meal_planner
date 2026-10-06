from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Ration, User


async def generate(db: AsyncSession, user: User, tags: list[str], period_days: int) -> Ration:
    """Создаёт пустой рацион-заготовку для последующего генератора блюд."""
    ration = Ration(user_id=user.id, tags=tags, period_days=period_days, status="draft")
    db.add(ration)
    await db.flush()
    return ration
