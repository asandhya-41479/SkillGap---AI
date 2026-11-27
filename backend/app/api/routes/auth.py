import math

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.login_limiter import login_limiter
from app.core.security import create_access_token
from app.db.database import get_db
from app.db.database import SessionLocal
from app.schemas.user import (
    ForgotPasswordRequest, MessageResponse, ResetPasswordRequest, Token, UserLogin, UserRegister, UserResponse,
)
from app.services import password_reset_service
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


FORGOT_MESSAGE = "If an account exists for this email, we have sent a link to reset the password."


def _send_reset_in_background(email: str) -> None:
    """Runs after the response is sent, in its own database session, so the response time is the same
    for registered and unknown emails."""
    db = SessionLocal()
    try:
        password_reset_service.request_reset(db, email)
    finally:
        db.close()


@router.post("/forgot-password", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED)
def forgot_password(data: ForgotPasswordRequest, background: BackgroundTasks):
    background.add_task(_send_reset_in_background, data.email)
    return MessageResponse(detail=FORGOT_MESSAGE)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        password_reset_service.reset_password(db, data.token, data.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
