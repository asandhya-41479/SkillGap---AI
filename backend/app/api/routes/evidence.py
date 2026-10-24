from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.readiness import EvidenceCreate, EvidenceResponse
from app.services import evidence_service as svc

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post("", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
def add_evidence(data: EvidenceCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ev, detail = svc.add_evidence(db, user.id, data)
    return svc.to_response(ev, detail)


@router.get("", response_model=list[EvidenceResponse])
def list_evidence(skill_name: str | None = Query(default=None, max_length=100),
                  user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [svc.to_response(e) for e in svc.list_evidence(db, user.id, skill_name)]


@router.get("/{evidence_id}", response_model=EvidenceResponse)
def get_evidence(evidence_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.to_response(svc.get_evidence(db, user.id, evidence_id))


@router.post("/{evidence_id}/verify", response_model=EvidenceResponse)
def verify_evidence(evidence_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ev, detail = svc.reverify(db, user.id, evidence_id)
    return svc.to_response(ev, detail)


@router.delete("/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evidence(evidence_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    svc.delete_evidence(db, user.id, evidence_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)