from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user
from app.db.session import get_db
from app.models import Meal, Ration, RationMeal, Tracking, User

router = APIRouter(prefix="/diary", tags=["diary"])


class DiaryEntry(BaseModel):
    id: str
    user_id: str
    entry_date: date
    meal_type: str
    meal_id: str
    calories: float
    note: str | None = None
    completed: bool


class DiaryCreate(BaseModel):
    entry_date: date
    meal_type: str
    meal_id: str | None = None
    calories: float = 0
    note: str | None = None
    completed: bool = False


async def rows_for_user(db: AsyncSession, user: User):
    return (await db.execute(select(Tracking, RationMeal, Meal).join(RationMeal, RationMeal.id == Tracking.ration_meal_id)
                             .join(Meal, Meal.id == RationMeal.meal_id)
                             .where(Tracking.user_id == user.id).order_by(RationMeal.date, RationMeal.meal_type))).all()


def as_entry(user: User, tracking: Tracking, ration_meal: RationMeal, meal: Meal):
    return DiaryEntry(id=tracking.id, user_id=user.id, entry_date=ration_meal.date, meal_type=ration_meal.meal_type,
                      meal_id=meal.id, calories=float(meal.calories), completed=tracking.status == "eaten",
                      note=tracking.status if tracking.status != "planned" else None)


@router.get("", response_model=list[DiaryEntry])
async def list_diary(db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return [as_entry(user, *row) for row in await rows_for_user(db, user)]


@router.post("", response_model=DiaryEntry, status_code=201)
async def create_diary(data: DiaryCreate, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    query = select(RationMeal).join(Ration, Ration.id == RationMeal.ration_id).where(
        Ration.user_id == user.id, RationMeal.date == data.entry_date, RationMeal.meal_type == data.meal_type)
    if data.meal_id:
        query = query.where(RationMeal.meal_id == data.meal_id)
    ration_meal = (await db.execute(query)).scalar_one_or_none()
    if ration_meal is None:
        raise HTTPException(404, "Приём пищи не найден в рационе на эту дату")
    tracking = (await db.execute(select(Tracking).where(Tracking.user_id == user.id,
                                                       Tracking.ration_meal_id == ration_meal.id))).scalar_one_or_none()
    if tracking is None:
        tracking = Tracking(user_id=user.id, ration_meal_id=ration_meal.id)
        db.add(tracking)
    tracking.status = "eaten" if data.completed else "planned"
    tracking.eaten_at = datetime.now(timezone.utc) if data.completed else None
    await db.commit()
    await db.refresh(tracking)
    meal = await db.get(Meal, ration_meal.meal_id)
    return as_entry(user, tracking, ration_meal, meal)


@router.patch("/{entry_id}", response_model=DiaryEntry)
async def update_diary(entry_id: str, data: DiaryCreate, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    tracking = await db.get(Tracking, entry_id)
    if tracking is None or tracking.user_id != user.id:
        raise HTTPException(404, "Запись не найдена")
    ration_meal = await db.get(RationMeal, tracking.ration_meal_id)
    if ration_meal.date != data.entry_date or ration_meal.meal_type != data.meal_type:
        raise HTTPException(400, "Нельзя изменить дату или приём пищи существующей записи")
    tracking.status = "eaten" if data.completed else "planned"
    tracking.eaten_at = datetime.now(timezone.utc) if data.completed else None
    await db.commit()
    await db.refresh(tracking)
    return as_entry(user, tracking, ration_meal, await db.get(Meal, ration_meal.meal_id))


@router.delete("/{entry_id}", status_code=204)
async def delete_diary(entry_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    tracking = await db.get(Tracking, entry_id)
    if tracking is None or tracking.user_id != user.id:
        raise HTTPException(404, "Запись не найдена")
    await db.delete(tracking)
    await db.commit()
