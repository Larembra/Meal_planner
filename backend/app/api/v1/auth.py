from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user
from app.core.config import settings
from app.core.security import create_token, decode_token, hash_password, token_expiry, verify_password
from app.db.session import get_db
from app.models import RefreshToken, User
from app.schemas.schemas import LoginRequest, RefreshRequest, TokenResponse, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


async def issue_tokens(db: AsyncSession, user: User) -> TokenResponse:
    refresh = create_token(user.id, "refresh", timedelta(days=settings.refresh_token_expire_days))
    payload = decode_token(refresh)
    db.add(RefreshToken(user_id=user.id, jti=payload["jti"], expires_at=token_expiry(settings.refresh_token_expire_days)))
    access = create_token(user.id, "access", timedelta(minutes=settings.access_token_expire_minutes))
    await db.commit()
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/register", response_model=UserRead, status_code=201)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Регистрирует пользователя."""
    if (await db.execute(select(User).where(User.email == data.email))).scalar_one_or_none():
        raise HTTPException(409, "Email уже зарегистрирован")
    values = data.model_dump(exclude={"password"})
    user = User(**values, hashed_password=hash_password(data.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Выдаёт пару JWT-токенов."""
    user = (await db.execute(select(User).where(User.email == data.email))).scalar_one_or_none()
    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(401, "Неверный email или пароль")
    return await issue_tokens(db, user)


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(current_user)):
    """Возвращает текущего авторизованного пользователя."""
    return user


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Обновляет access-токен и ротирует refresh-токен."""
    try:
        payload = decode_token(data.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError
    except Exception:
        raise HTTPException(401, "Недействительный refresh-токен")
    stored = (await db.execute(select(RefreshToken).where(RefreshToken.jti == payload.get("jti")))).scalar_one_or_none()
    if stored is None or stored.revoked or stored.expires_at.timestamp() < __import__("time").time():
        raise HTTPException(401, "Refresh-токен отозван или истёк")
    stored.revoked = True
    user = await db.get(User, str(payload["sub"]))
    if user is None:
        raise HTTPException(401, "Пользователь не найден")
    return await issue_tokens(db, user)


@router.post("/logout")
async def logout(data: RefreshRequest, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    """Отзывает refresh-токен."""
    try:
        payload = decode_token(data.refresh_token)
        stored = (await db.execute(select(RefreshToken).where(RefreshToken.jti == payload.get("jti"), RefreshToken.user_id == user.id))).scalar_one_or_none()
        if stored:
            stored.revoked = True
            await db.commit()
    except Exception:
        return {"detail": "Выход выполнен"}
    return {"detail": "Выход выполнен"}
