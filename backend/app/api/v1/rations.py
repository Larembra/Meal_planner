from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user
from app.db.session import get_db
from app.models import Ration, User
from app.schemas.schemas import RationCreate, RationRead
from app.services.generator import generate

router = APIRouter(prefix="/rations", tags=["rations"])


@router.post("/generate", response_model=RationRead, status_code=201)
async def generate_ration(data: RationCreate, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    ration = await generate(db, user, data.tags, data.period_days)
    await db.commit()
    await db.refresh(ration)
    return ration


@router.get("", response_model=list[RationRead])
async def list_rations(db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return list((await db.execute(select(Ration).where(Ration.user_id == user.id).order_by(Ration.created_at.desc()))).scalars())


@router.get("/{ration_id}", response_model=RationRead)
async def get_ration(ration_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    ration = await db.get(Ration, ration_id)
    if ration is None or ration.user_id != user.id:
        raise HTTPException(404, "Рацион не найден")
    return ration


@router.get("/{ration_id}/plan", response_model=RationRead)
async def ration_plan(ration_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await get_ration(ration_id, db, user)


@router.delete("/{ration_id}", status_code=204)
async def delete_ration(ration_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    ration = await db.get(Ration, ration_id)
    if ration is None or ration.user_id != user.id:
        raise HTTPException(404, "Рацион не найден")
    await db.delete(ration)
    await db.commit()


@router.post("/{ration_id}/replace", response_model=RationRead)
async def replace_ration(ration_id: str, data: RationCreate, db: AsyncSession = Depends(get_db),
                         user: User = Depends(current_user)):
    old = await db.get(Ration, ration_id)
    if old is None or old.user_id != user.id:
        raise HTTPException(404, "Рацион не найден")
    await db.delete(old)
    await db.flush()
    ration = await generate(db, user, data.tags, data.period_days)
    await db.commit()
    await db.refresh(ration)
    return ration
