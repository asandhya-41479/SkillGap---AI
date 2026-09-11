from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.skill import UserSkill
from app.schemas.skill import EvidenceItem, SkillCreate, SkillProfileItem, SkillUpdate
from app.services.skill_normalization import normalize_skill_name


def create_skill(db: Session, user_id: int, skill_in: SkillCreate) -> UserSkill:
    normalized_name = normalize_skill_name(skill_in.skill_name)

    skill = UserSkill(
        user_id=user_id,
        skill_name=normalized_name,
        category=skill_in.category,
        self_assessed_level=skill_in.self_assessed_level,
        is_manual=True,
    )
    db.add(skill)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have this skill in your profile.",
        )
    db.refresh(skill)
    return skill



def get_user_skills(db: Session, user_id: int) -> list[UserSkill]:
    return (
        db.query(UserSkill)
        .filter(UserSkill.user_id == user_id)
        .order_by(UserSkill.skill_name)
        .all()
    )


def get_owned_skill(db: Session, user_id: int, skill_id: int) -> UserSkill:
    skill = (
        db.query(UserSkill)
        .filter(UserSkill.id == skill_id, UserSkill.user_id == user_id)
        .first()
    )
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found.")
    return skill


def update_skill(db: Session, user_id: int, skill_id: int, update_data: SkillUpdate) -> UserSkill:
    skill = get_owned_skill(db, user_id, skill_id)

    if update_data.category is not None:
        skill.category = update_data.category
    if update_data.self_assessed_level is not None:
        skill.self_assessed_level = update_data.self_assessed_level

    db.commit()
    db.refresh(skill)
    return skill



def delete_skill(db: Session, user_id: int, skill_id: int) -> None:
    skill = get_owned_skill(db, user_id, skill_id)
    db.delete(skill)
    db.commit()


def get_skill_profile(db: Session, user_id: int) -> list[SkillProfileItem]:
    skills = get_user_skills(db, user_id)
    profile = []
    for skill in skills:
        sources = (["manual"] if skill.is_manual else []) + (["github"] if skill.evidence else [])
        profile.append(SkillProfileItem(
            skill_name=skill.skill_name,
            category=skill.category,
            self_assessed_level=skill.self_assessed_level,
            demonstrated=bool(skill.evidence),
            evidence_count=len(skill.evidence),
            evidence=[EvidenceItem.model_validate(e) for e in skill.evidence],
            sources=sources or ["manual"],
        ))
    return profile