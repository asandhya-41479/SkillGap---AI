from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import PasswordChange, UserResponse, UserUpdate
from app.services.user_service import change_password, update_user

router = APIRouter(prefix="/users", tags=["USERS"])


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
def update_current_user(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated_user = update_user(db, current_user, update_data)
    return updated_user


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_my_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    change_password(db, current_user, data)
