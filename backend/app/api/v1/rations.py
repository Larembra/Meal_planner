from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user
from app.api.v1.catalog import meal_payload
from app.db.session import get_db
from app.models import Meal, Ration, RationMeal, User
from app.schemas.schemas import RationCreate, RationRead
from app.services.generator import generate

router = APIRouter(prefix="/rations", tags=["rations"])


class RationMealCreate(BaseModel):
    meal_id: str
    date: date
    meal_type: str
    servings: float = 1


@router.post("/generate", response_model=RationRead, status_code=201)
async def generate_ration(data: RationCreate, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    ration = await generate(db, user, data.tags, data.period_days, data.extra_request, data.model)
    await db.commit()
    await db.refresh(ration)
    return ration


@router.get("", response_model=list[RationRead])
async def list_rations(db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return list((await db.execute(select(Ration).where(Ration.user_id == user.id).order_by(Ration.created_at.desc()))).scalars())


async def owned_ration(ration_id: str, db: AsyncSession, user: User) -> Ration:
    ration = await db.get(Ration, ration_id)
    if ration is None or ration.user_id != user.id:
        raise HTTPException(404, "Рацион не найден")
    return ration


@router.get("/{ration_id}", response_model=RationRead)
async def get_ration(ration_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await owned_ration(ration_id, db, user)


@router.get("/{ration_id}/plan")
async def ration_plan(ration_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    ration = await owned_ration(ration_id, db, user)
    meal_order = case(
        (RationMeal.meal_type == "breakfast", 1),
        (RationMeal.meal_type == "second_breakfast", 2),
        (RationMeal.meal_type == "lunch", 3),
        (RationMeal.meal_type == "snack", 4),
        (RationMeal.meal_type == "dinner", 5),
        else_=6,
    )
    rows = (await db.execute(select(RationMeal, Meal).join(Meal, Meal.id == RationMeal.meal_id)
                             .where(RationMeal.ration_id == ration.id).order_by(RationMeal.date, meal_order))).all()
    return {"ration": RationRead.model_validate(ration), "meals": [
        {**(await meal_payload(db, meal)), "ration_meal_id": rm.id, "date": rm.date,
         "meal_type": rm.meal_type, "servings": float(rm.servings)}
        for rm, meal in rows]}


@router.post("/{ration_id}/meals", status_code=201)
async def add_ration_meal(ration_id: str, data: RationMealCreate,
                          db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    ration = await owned_ration(ration_id, db, user)
    meal = await db.get(Meal, data.meal_id)
    if meal is None or meal.status != "published":
        raise HTTPException(404, "Блюдо не найдено")
    existing = (await db.execute(select(RationMeal).where(
        RationMeal.ration_id == ration.id,
        RationMeal.date == data.date,
        RationMeal.meal_type == data.meal_type,
    ))).scalar_one_or_none()
    if existing:
        existing.meal_id = meal.id
        existing.servings = data.servings
    else:
        existing = RationMeal(ration_id=ration.id, meal_id=meal.id, date=data.date,
                              meal_type=data.meal_type, servings=data.servings)
        db.add(existing)
    await db.commit()
    await db.refresh(existing)
    return {"id": existing.id, "meal_id": existing.meal_id, "date": existing.date,
            "meal_type": existing.meal_type, "servings": float(existing.servings)}


@router.delete("/{ration_id}", status_code=204)
async def delete_ration(ration_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    ration = await owned_ration(ration_id, db, user)
    await db.delete(ration)
    await db.commit()


@router.post("/{ration_id}/replace", response_model=RationRead)
async def replace_ration(ration_id: str, data: RationCreate, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    ration = await owned_ration(ration_id, db, user)
    await db.delete(ration)
    await db.flush()
    replacement = await generate(db, user, data.tags, data.period_days, data.extra_request, data.model)
    await db.commit()
    await db.refresh(replacement)
    return replacement
