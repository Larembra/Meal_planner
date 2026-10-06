from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user
from app.db.session import get_db
from app.models import Dish, User
from app.schemas.schemas import DishRead

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("", response_model=list[DishRead])
async def list_recipes(category: Optional[str] = Query(None), tag: Optional[str] = Query(None),
                        db: AsyncSession = Depends(get_db), _: User = Depends(current_user)):
    query = select(Dish).where(Dish.ration_id.is_not(None))
    if category:
        query = query.where(Dish.category == category)
    if tag:
        query = query.where(Dish.tag == tag)
    return list((await db.execute(query.order_by(Dish.id))).scalars())


@router.get("/{recipe_id}", response_model=DishRead)
async def get_recipe(recipe_id: str, db: AsyncSession = Depends(get_db), _: User = Depends(current_user)):
    recipe = await db.get(Dish, recipe_id)
    if recipe is None:
        raise HTTPException(404, "Рецепт не найден")
    return recipe


@router.get("/{recipe_id}/recipe")
async def get_recipe_details(recipe_id: str, db: AsyncSession = Depends(get_db), _: User = Depends(current_user)):
    recipe = await db.get(Dish, recipe_id)
    if recipe is None:
        raise HTTPException(404, "Рецепт не найден")
    return recipe.recipe or {}
