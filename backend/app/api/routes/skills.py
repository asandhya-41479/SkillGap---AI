from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.skill import SkillCreate, SkillResponse, SkillUpdate
from app.services import skill_service

router = APIRouter(prefix="/skills", tags=["skills"])


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
def add_skill(
    skill_in: SkillCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return skill_service.create_skill(db, current_user.id, skill_in)


@router.get("", response_model=list[SkillResponse])
def list_skills(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return skill_service.get_user_skills(db, current_user.id)


@router.put("/{skill_id}", response_model=SkillResponse)
def edit_skill(
    skill_id: int,

    update_data: SkillUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return skill_service.update_skill(db, current_user.id, skill_id, update_data)


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    skill_service.delete_skill(db, current_user.id, skill_id)