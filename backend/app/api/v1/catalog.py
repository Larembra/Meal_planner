from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models import Meal, MealProduct, Product

router = APIRouter(tags=["catalog"])

DEFAULT_IMAGES = {
    "breakfast": "https://images.unsplash.com/photo-1490474418585-ba9bad8fd0ea?auto=format&fit=crop&w=1200&q=85",
    "lunch": "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=1200&q=85",
    "dinner": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1200&q=85",
    "snack": "https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=1200&q=85",
}


async def meal_payload(db: AsyncSession, meal: Meal) -> dict:
    rows = (await db.execute(select(Product, MealProduct.quantity).join(MealProduct, MealProduct.product_id == Product.id)
                             .where(MealProduct.meal_id == meal.id).order_by(Product.name))).all()
    ingredients = [{"product_id": p.id, "name": p.name, "quantity": float(q), "unit": p.unit,
                    "price": float(p.cost), "category": p.category} for p, q in rows]
    category = {"breakfast": "Завтрак", "lunch": "Обед", "dinner": "Ужин", "snack": "Перекус"}.get(meal.meal_type, meal.meal_type)
    return {"id": meal.id, "name": meal.name, "description": meal.description, "meal_type": meal.meal_type,
            "cooking_time": meal.cooking_time, "servings": meal.servings, "calories": float(meal.calories),
            "protein": float(meal.protein), "fat": float(meal.fat), "carbs": float(meal.carbs),
            "diet_type": meal.diet_type, "allergens": meal.allergens or [], "tags": meal.tags or [],
            "cost": float(meal.cost), "ingredients": ingredients, "products": ingredients,
            # Compatibility aliases for the existing React client.
            "title": meal.name, "category": category, "time": meal.cooking_time,
            "proteins": float(meal.protein), "fats": float(meal.fat), "price": float(meal.cost),
            "image_url": meal.image_url or DEFAULT_IMAGES.get(meal.meal_type, DEFAULT_IMAGES["lunch"]),
            "recipe": {"description": meal.description, "ingredients": ingredients,
                                           "steps": [], "tag": ", ".join(meal.tags or []), "time": meal.cooking_time}}


@router.get("/dishes")
async def dishes(meal_type: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    query = select(Meal).where(Meal.status == "published")
    if meal_type:
        query = query.where(Meal.meal_type == meal_type)
    rows = (await db.execute(query.order_by(Meal.name))).scalars().all()
    return [await meal_payload(db, meal) for meal in rows]


@router.get("/dishes/{dish_id}")
async def dish(dish_id: str, db: AsyncSession = Depends(get_db)):
    meal = await db.get(Meal, dish_id)
    if meal is None or meal.status != "published":
        raise HTTPException(404, "Блюдо не найдено")
    return await meal_payload(db, meal)


@router.get("/dishes/{dish_id}/recipe")
async def dish_recipe(dish_id: str, db: AsyncSession = Depends(get_db)):
    return await dish(dish_id, db)


@router.get("/products")
async def products(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Product).order_by(Product.name))).scalars().all()
    return [{"id": p.id, "name": p.name, "category": p.category, "unit": p.unit,
             "calories": float(p.calories), "protein": float(p.protein), "fat": float(p.fat),
             "carbs": float(p.carbs), "cost": float(p.cost)} for p in rows]
