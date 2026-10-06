from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user, require_roles
from app.db.session import get_db
from app.models import Application, User
from app.schemas.schemas import ApplicationCreate, ApplicationRead

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationRead, status_code=201)
async def create_application(data: ApplicationCreate, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    application = Application(**data.model_dump(), user_id=user.id)
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return application


@router.get("", response_model=list[ApplicationRead])
async def my_applications(db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return list((await db.execute(select(Application).where(Application.user_id == user.id)
                                  .order_by(Application.created_at.desc()))).scalars())

@router.get("/{application_id}", response_model=ApplicationRead)
async def get_application(application_id: str, db: AsyncSession = Depends(get_db),
                           user: User = Depends(current_user)):
    application = await db.get(Application, application_id)
    if application is None or application.user_id != user.id:
        raise HTTPException(404, "Заявка не найдена")
    return application


@router.patch("/{application_id}", response_model=ApplicationRead)
async def update_application(application_id: str, data: ApplicationCreate,
                             db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    application = await db.get(Application, application_id)
    if application is None or application.user_id != user.id:
        raise HTTPException(404, "Заявка не найдена")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(application, key, value)
    await db.commit()
    await db.refresh(application)
    return application


@router.delete("/{application_id}", status_code=204)
async def delete_application(application_id: str, db: AsyncSession = Depends(get_db),
                             user: User = Depends(current_user)):
    application = await db.get(Application, application_id)
    if application is None or application.user_id != user.id:
        raise HTTPException(404, "Заявка не найдена")
    await db.delete(application)
    await db.commit()
