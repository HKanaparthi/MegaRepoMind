from fastapi import Cookie, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.core.security import get_user_id_from_token
from app.models.user import User
from typing import Annotated
from fastapi import Depends


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    access_token: str = Cookie(default=None),
) -> User:
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = get_user_id_from_token(access_token)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
