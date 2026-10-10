from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user
from app.core.config import settings
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.db.session import get_db
from app.models import Profile, User
from app.schemas.schemas import LoginRequest, RefreshRequest, TokenResponse, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


def read_user(user: User, profile: Optional[Profile] = None) -> UserRead:
    preferences = {}
    if profile:
        preferences = {"diet": profile.diet_type, "meals_per_day": profile.meals_per_day,
                       "budget": float(profile.budget) if profile.budget is not None else None,
                       "text": profile.preferences or ""}
    return UserRead(id=user.id, email=user.email, name=user.name, role=user.role,
                    goal=profile.goal if profile else None,
                    allergies=[item.strip() for item in (profile.restrictions or "").split(",") if item.strip()] if profile else [],
                    preferences=preferences, cooking_time_minutes=profile.max_cooking_time if profile else None,
                    created_at=user.created_at, updated_at=user.updated_at)


def issue_tokens(user_id: str) -> TokenResponse:
    return TokenResponse(
        access_token=create_token(user_id, "access", timedelta(minutes=settings.access_token_expire_minutes)),
        refresh_token=create_token(user_id, "refresh", timedelta(days=settings.refresh_token_expire_days)),
    )


@router.post("/register", response_model=UserRead, status_code=201)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    email = str(data.email).lower()
    if (await db.execute(select(User).where(User.email == email))).scalar_one_or_none():
        raise HTTPException(409, "Email уже зарегистрирован")
    user = User(email=email, name=data.name, hashed_password=hash_password(data.password), role="user")
    db.add(user)
    await db.flush()
    profile = Profile(user_id=user.id)
    db.add(profile)
    await db.commit()
    await db.refresh(user)
    return read_user(user, profile)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.email == str(data.email).lower()))).scalar_one_or_none()
    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(401, "Неверный email или пароль")
    return issue_tokens(user.id)


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    profile = (await db.execute(select(Profile).where(Profile.user_id == user.id))).scalar_one_or_none()
    return read_user(user, profile)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest):
    try:
        payload = decode_token(data.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError
    except Exception:
        raise HTTPException(401, "Недействительный refresh-токен")
    return issue_tokens(str(payload["sub"]))


@router.post("/logout")
async def logout():
    # The bundled schema has no refresh-token table; clients discard their JWTs.
    return {"detail": "Выход выполнен"}
