"""Заполняет базу демонстрационными пользователями, рецептами и рационом."""
import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Application, Dish, FoodDiary, Product, Ration, User


RECIPES = [
    ("Куриное филе с брокколи", "Ужин", 380, 42, 18, 8),
    ("Творожная запеканка", "Завтрак", 310, 28, 12, 30),
    ("Тыквенный суп-пюре", "Обед", 240, 6, 10, 30),
    ("Салат с тунцом", "Перекус", 290, 24, 14, 12),
    ("Запеченная треска", "Ужин", 320, 34, 12, 14),
]


async def main() -> None:
    """Создаёт демонстрационные данные, если они ещё не существуют."""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with SessionLocal() as db:
        client = (await db.execute(select(User).where(User.email == "client@test.ru"))).scalar_one_or_none()
        if client is None:
            client = User(email="client@test.ru", name="Клиент", role="client",
                          hashed_password=hash_password("password123"))
            db.add(client)
        moderator = (await db.execute(select(User).where(User.email == "moderator@test.ru"))).scalar_one_or_none()
        if moderator is None:
            moderator = User(email="moderator@test.ru", name="Модератор", role="moderator",
                             hashed_password=hash_password("password123"))
            db.add(moderator)
        await db.flush()

        ration = (await db.execute(select(Ration).where(Ration.user_id == client.id))).scalar_one_or_none()
        if ration is None:
            ration = Ration(user_id=client.id, period_days=1, tags=["баланс"],
                            status="active", total_calories=1540, total_protein=134,
                            total_fat=66, total_carbs=94, total_price=1200)
            db.add(ration)
            await db.flush()
            for index, (name, meal_type, calories, proteins, fats, carbs) in enumerate(RECIPES[:4]):
                dish = Dish(ration_id=ration.id, name=name, meal_type=meal_type, day_number=1,
                            macros={"protein": proteins, "fat": fats, "carbs": carbs},
                            recipe={"steps": ["Подготовить продукты", "Приготовить до готовности"]},
                            calories=calories, proteins=proteins, fats=fats, carbs=carbs, price=200)
                db.add(dish)
                await db.flush()
                db.add(Product(dish_id=dish.id, name="Основной продукт", quantity=200,
                               unit="г", calories_per_100g=100))

        if not (await db.execute(select(Application).where(Application.user_id == client.id))).first():
            db.add(Application(user_id=client.id, ration_id=ration.id, status="active",
                               items=[{"name": "Продукты на день", "quantity": 1}]))
        if not (await db.execute(select(FoodDiary).where(FoodDiary.user_id == client.id))).first():
            for meal_type in ("Завтрак", "Обед", "Ужин"):
                db.add(FoodDiary(user_id=client.id, entry_date="2026-10-06",
                                 meal_type=meal_type, calories=350, completed=True))
        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())
