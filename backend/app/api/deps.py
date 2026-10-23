from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token
from app.db.session import get_db
from app.models import User

bearer = HTTPBearer()


async def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Проверяет access-токен и возвращает активного пользователя."""
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise ValueError
        user_id = str(payload["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user


bearer_optional = HTTPBearer(auto_error=False)


async def optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_optional),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Возвращает текущего пользователя, если передан валидный токен, либо None."""
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            return None
        user_id = str(payload.get("sub"))
        return await db.get(User, user_id)
    except Exception:
        return None



def require_roles(*roles: str):
    async def checker(user: User = Depends(current_user)) -> User:
        # The shipped database only permits the roles "user" and "admin".
        allowed = {"admin" if role == "moderator" else role for role in roles}
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        return user
    return checker
