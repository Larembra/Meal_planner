from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user, require_roles
from app.api.v1.auth import read_user
from app.db.session import get_db
from app.models import Profile, User
from app.schemas.schemas import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])
profile_router = APIRouter(prefix="/profile", tags=["profile"])


async def get_profile_row(db: AsyncSession, user_id: str) -> Profile:
    profile = (await db.execute(select(Profile).where(Profile.user_id == user_id))).scalar_one_or_none()
    if profile is None:
        profile = Profile(user_id=user_id)
        db.add(profile)
        await db.flush()
    return profile


async def get_user_read(db: AsyncSession, user: User) -> UserRead:
    return read_user(user, await get_profile_row(db, user.id))


async def apply_profile(data: UserUpdate, db: AsyncSession, user: User) -> UserRead:
    values = data.model_dump(exclude_unset=True)
    if "name" in values:
        user.name = values["name"]
    profile = await get_profile_row(db, user.id)
    if "goal" in values:
        profile.goal = values["goal"]
    if "allergies" in values:
        profile.restrictions = ", ".join(values["allergies"] or [])
    if "cooking_time_minutes" in values:
        profile.max_cooking_time = values["cooking_time_minutes"]
    if "preferences" in values:
        prefs = values["preferences"] or {}
        if "diet" in prefs:
            profile.diet_type = prefs["diet"]
        if "meals_per_day" in prefs and prefs["meals_per_day"] is not None:
            profile.meals_per_day = prefs["meals_per_day"]
        if "budget" in prefs:
            profile.budget = prefs["budget"]
        if "text" in prefs:
            profile.preferences = prefs["text"] or ""
    await db.commit()
    await db.refresh(user)
    await db.refresh(profile)
    return read_user(user, profile)


@router.get("/me", response_model=UserRead)
async def get_me(db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await get_user_read(db, user)


@router.get("/profile", response_model=UserRead)
@router.get("/me/profile", response_model=UserRead)
async def get_profile(db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await get_user_read(db, user)


@router.patch("/me", response_model=UserRead)
@router.patch("/profile", response_model=UserRead)
@router.patch("/me/profile", response_model=UserRead)
async def update_profile(data: UserUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await apply_profile(data, db, user)


@router.get("/me/stats")
async def profile_stats(db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    profile = await get_profile_row(db, user.id)
    return {"goal": profile.goal, "cooking_time_minutes": profile.max_cooking_time}


@router.get("", response_model=list[UserRead])
async def list_users(db: AsyncSession = Depends(get_db), _: User = Depends(require_roles("admin"))):
    users = (await db.execute(select(User).order_by(User.created_at.desc()))).scalars().all()
    return [await get_user_read(db, item) for item in users]


@profile_router.get("", response_model=UserRead)
async def profile(db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await get_user_read(db, user)


@profile_router.patch("", response_model=UserRead)
async def patch_profile(data: UserUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await apply_profile(data, db, user)
