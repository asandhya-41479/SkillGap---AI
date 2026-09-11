from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.skill import SkillProfileItem
from app.services.skill_service import get_skill_profile

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/skills", response_model=list[SkillProfileItem])
def profile_skills(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_skill_profile(db, current_user.id)