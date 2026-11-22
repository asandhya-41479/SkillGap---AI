import math

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.login_limiter import login_limiter
from app.core.security import create_access_token
from app.db.database import get_db
from app.schemas.user import Token, UserLogin, UserRegister, UserResponse
from app.services.user_service import authenticate_user, create_user, get_user_by_email

router = APIRouter(prefix="/auth", tags=["AUTH"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = create_user(db, user_data)
    return new_user


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    wait = login_limiter.retry_after(credentials.email)
    if wait:
        minutes = math.ceil(wait / 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Please try again in {minutes} minute{'s' if minutes != 1 else ''}.",
            headers={"Retry-After": str(wait)},
        )

    user = authenticate_user(db, credentials.email, credentials.password)
    if user is None:
        login_limiter.record_failure(credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    login_limiter.reset(credentials.email)
    access_token = create_access_token(user_id=user.id)
    return Token(access_token=access_token)