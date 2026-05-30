from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models import User
from ..schemas import UserRegister, UserLogin, TokenResponse, UserOut
from ..auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: UserRegister, db: AsyncSession = Depends(get_db)):
    normalized_email = body.email.strip().lower()
    existing = await db.execute(select(User).where(User.email == normalized_email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=normalized_email,
        password_hash=hash_password(body.password),
        ui_language=body.ui_language,
    )
    db.add(user)
    await db.flush()
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id, user.email)
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    normalized_email = body.email.strip().lower()
    result = await db.execute(select(User).where(User.email == normalized_email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.id, user.email)
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user
