from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.roadmap import (
    RoadmapCreate, RoadmapDetailResponse, RoadmapItemResponse, RoadmapItemStatusUpdate,
    RoadmapProgress, RoadmapRegenerate, RoadmapSummaryResponse,
)
from app.services.roadmap import roadmap_service as svc

router = APIRouter(prefix="/roadmaps", tags=["roadmaps"])


@router.post("", response_model=RoadmapDetailResponse, status_code=status.HTTP_201_CREATED)
def create_roadmap(data: RoadmapCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.to_detail(db, svc.generate_and_store(db, user.id, data))


@router.post("/{roadmap_id}/regenerate", response_model=RoadmapDetailResponse, status_code=status.HTTP_201_CREATED)
def regenerate_roadmap(roadmap_id: int, data: RoadmapRegenerate, user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    return svc.to_detail(db, svc.regenerate(db, user.id, roadmap_id, data))


@router.get("", response_model=list[RoadmapSummaryResponse])
def list_roadmaps(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [svc.to_summary(r) for r in svc.list_roadmaps(db, user.id)]


@router.get("/{roadmap_id}", response_model=RoadmapDetailResponse)

def get_roadmap(roadmap_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.to_detail(db, svc.get_roadmap(db, user.id, roadmap_id))


@router.get("/{roadmap_id}/progress", response_model=RoadmapProgress)
def get_progress(roadmap_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.progress(svc.get_roadmap(db, user.id, roadmap_id))


@router.patch("/{roadmap_id}/items/{item_id}", response_model=RoadmapItemResponse)
def set_item_status(roadmap_id: int, item_id: int, data: RoadmapItemStatusUpdate,
                    user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.update_item_status(db, user.id, roadmap_id, item_id, data.status)


@router.delete("/{roadmap_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_roadmap(roadmap_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    svc.delete_roadmap(db, user.id, roadmap_id)