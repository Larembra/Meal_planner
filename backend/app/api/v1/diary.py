from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user
from app.db.session import get_db
from app.models import FoodDiary, User
from app.schemas.schemas import DiaryCreate, DiaryRead

router = APIRouter(prefix="/diary", tags=["diary"])


@router.get("", response_model=list[DiaryRead])
async def list_diary(db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return list((await db.execute(select(FoodDiary).where(FoodDiary.user_id == user.id))).scalars())


@router.post("", response_model=DiaryRead, status_code=201)
async def create_diary(data: DiaryCreate, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    entry = FoodDiary(**data.model_dump(), user_id=user.id)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.patch("/{entry_id}", response_model=DiaryRead)
async def update_diary(entry_id: str, data: DiaryCreate, db: AsyncSession = Depends(get_db),
                       user: User = Depends(current_user)):
    entry = await db.get(FoodDiary, entry_id)
    if entry is None or entry.user_id != user.id:
        raise HTTPException(404, "Запись не найдена")
    for key, value in data.model_dump().items():
        setattr(entry, key, value)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=204)
async def delete_diary(entry_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    entry = await db.get(FoodDiary, entry_id)
    if entry is None or entry.user_id != user.id:
        raise HTTPException(404, "Запись не найдена")
    await db.delete(entry)
    await db.commit()
