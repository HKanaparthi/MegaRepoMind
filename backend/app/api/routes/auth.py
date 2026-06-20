import uuid
from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, UserOut, TokenResponse
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, get_user_id_from_token
)
from app.core.config import settings
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_tokens(response: Response, user_id: str):
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    secure = settings.ENVIRONMENT == "production"
    response.set_cookie("access_token", access_token, httponly=True, secure=secure,
                        samesite="lax", max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=secure,
                        samesite="lax", max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400)
    return access_token


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        id=str(uuid.uuid4()),
        email=body.email,
        name=body.name,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = _set_tokens(response, user.id)
    return TokenResponse(access_token=access_token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = _set_tokens(response, user.id)
    return TokenResponse(access_token=access_token, user=UserOut.model_validate(user))


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh(response: Response, refresh_token: str = Cookie(default=None), db: AsyncSession = Depends(get_db)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    user_id = get_user_id_from_token(refresh_token, token_type="refresh")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    access_token = _set_tokens(response, user.id)
    return TokenResponse(access_token=access_token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def me(access_token: str = Cookie(default=None), db: AsyncSession = Depends(get_db)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = get_user_id_from_token(access_token)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return UserOut.model_validate(user)
