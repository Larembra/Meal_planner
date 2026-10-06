from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user, require_roles
from app.db.session import get_db
from app.models import User
from app.schemas.schemas import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])
profile_router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=UserRead)
async def get_me(user: User = Depends(current_user)):
    return user


@router.get("/profile", response_model=UserRead)
async def get_profile(user: User = Depends(current_user)):
    """Возвращает профиль под именем, используемым клиентом."""
    return user


@router.patch("/me", response_model=UserRead)
async def update_me(data: UserUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/profile", response_model=UserRead)
async def update_profile(data: UserUpdate, db: AsyncSession = Depends(get_db),
                         user: User = Depends(current_user)):
    return await update_me(data, db, user)


@router.get("", response_model=list[UserRead])
async def list_users(db: AsyncSession = Depends(get_db), _: User = Depends(require_roles("admin"))):
    """Возвращает пользователей только администратору."""
    return list((await db.execute(select(User).order_by(User.id))).scalars())


@profile_router.get("", response_model=UserRead)
async def profile(user: User = Depends(current_user)):
    return user


@profile_router.patch("", response_model=UserRead)
async def patch_profile(data: UserUpdate, db: AsyncSession = Depends(get_db),
                        user: User = Depends(current_user)):
    return await update_me(data, db, user)


@router.get("/me/profile", response_model=UserRead)
async def me_profile(user: User = Depends(current_user)):
    return user


@router.patch("/me/profile", response_model=UserRead)
async def patch_me_profile(data: UserUpdate, db: AsyncSession = Depends(get_db),
                           user: User = Depends(current_user)):
    """Обновляет профиль текущего пользователя."""
    return await update_me(data, db, user)


@router.get("/me/stats")
async def profile_stats(db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return {"weight": user.weight, "height": user.height, "age": user.age,
            "goal": user.goal, "cooking_time_minutes": user.cooking_time_minutes}
