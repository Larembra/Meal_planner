from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user, require_roles
from app.db.session import get_db
from app.models import Dish, Product, User
from app.schemas.schemas import DishRead, ProductCreate, ProductRead

router = APIRouter(tags=["catalog"])


@router.get("/dishes", response_model=list[DishRead])
async def dishes(meal_type: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    query = select(Dish)
    if meal_type:
        query = query.where(Dish.meal_type == meal_type)
    return list((await db.execute(query.order_by(Dish.name))).scalars())


@router.get("/dishes/{dish_id}", response_model=DishRead)
async def dish(dish_id: str, db: AsyncSession = Depends(get_db)):
    value = await db.get(Dish, dish_id)
    if value is None:
        raise HTTPException(404, "Блюдо не найдено")
    return value


@router.get("/dishes/{dish_id}/recipe")
async def dish_recipe(dish_id: str, db: AsyncSession = Depends(get_db)):
    value = await db.get(Dish, dish_id)
    if value is None:
        raise HTTPException(404, "Блюдо не найдено")
    return value.recipe or {}


@router.get("/products", response_model=list[ProductRead])
async def products(db: AsyncSession = Depends(get_db)):
    return list((await db.execute(select(Product).order_by(Product.name))).scalars())


@router.post("/products", response_model=ProductRead, status_code=201)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db),
                         _: User = Depends(require_roles("admin", "moderator"))):
    value = Product(**data.model_dump())
    db.add(value)
    await db.commit()
    await db.refresh(value)
    return value
