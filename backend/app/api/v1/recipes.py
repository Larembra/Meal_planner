from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user
from app.api.v1.catalog import meal_payload
from app.db.session import get_db
from app.models import Meal, User

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("")
async def list_recipes(category: Optional[str] = Query(None), tag: Optional[str] = Query(None),
                       db: AsyncSession = Depends(get_db), _: User = Depends(current_user)):
    query = select(Meal).where(Meal.status == "published")
    if category:
        category = {"Завтрак": "breakfast", "Обед": "lunch", "Ужин": "dinner", "Перекус": "snack"}.get(category, category)
        query = query.where(Meal.meal_type == category)
    if tag:
        query = query.where(Meal.tags.contains([tag]))
    rows = (await db.execute(query.order_by(Meal.created_at.desc()))).scalars().all()
    return [await meal_payload(db, meal) for meal in rows]


@router.get("/{recipe_id}")
async def get_recipe(recipe_id: str, db: AsyncSession = Depends(get_db), _: User = Depends(current_user)):
    meal = await db.get(Meal, recipe_id)
    if meal is None or meal.status != "published":
        raise HTTPException(404, "Рецепт не найден")
    return await meal_payload(db, meal)


@router.get("/{recipe_id}/recipe")
async def get_recipe_details(recipe_id: str, db: AsyncSession = Depends(get_db), _: User = Depends(current_user)):
    value = await get_recipe(recipe_id, db, _)
    return value["recipe"]
