from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_user
from app import models, schemas

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=list[schemas.AnalysisSummaryOut])
def list_history(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    analyses = (
        db.query(models.AnalysisResult)
        .options(joinedload(models.AnalysisResult.medicines))
        .filter(models.AnalysisResult.user_id == user.id)
        .order_by(models.AnalysisResult.created_at.desc())
        .all()
    )
    return [
        schemas.AnalysisSummaryOut(
            id=a.id,
            source_type=a.source_type,
            source_label=a.source_label,
            medicine_names=[m.name for m in a.medicines],
            language=a.language,
            created_at=a.created_at,
        )
        for a in analyses
    ]


@router.get("/{analysis_id}", response_model=schemas.AnalysisOut)
def get_history_item(analysis_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    analysis = db.query(models.AnalysisResult).filter(
        models.AnalysisResult.id == analysis_id, models.AnalysisResult.user_id == user.id
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.delete("/{analysis_id}")
def delete_history_item(analysis_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    analysis = db.query(models.AnalysisResult).filter(
        models.AnalysisResult.id == analysis_id, models.AnalysisResult.user_id == user.id
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    db.delete(analysis)
    db.commit()
    return {"success": True}
