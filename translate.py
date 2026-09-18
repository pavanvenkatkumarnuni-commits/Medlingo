from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app import models, schemas
from app.services.ai_provider import get_provider, AIProviderError

router = APIRouter(prefix="/api/translate", tags=["translate"])


@router.post("/{analysis_id}", response_model=schemas.TranslationOut)
def translate_analysis(
    analysis_id: str,
    payload: schemas.TranslateRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    analysis = db.query(models.AnalysisResult).filter(
        models.AnalysisResult.id == analysis_id, models.AnalysisResult.user_id == user.id
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Serve a cached translation if we already made one for this language
    existing = next((t for t in analysis.translations if t.language == payload.language), None)
    if existing:
        return existing

    if payload.language == "en":
        return schemas.TranslationOut(
            language="en",
            translated_explanation=analysis.explanation_text or "",
            translated_terminology=analysis.terminology or [],
        )

    provider = get_provider()
    try:
        result = provider.translate(analysis.explanation_text or "", analysis.terminology or [], payload.language)
    except AIProviderError as e:
        raise HTTPException(status_code=502, detail=f"Translation failed: {e}")

    translation = models.Translation(
        analysis_id=analysis.id,
        language=payload.language,
        translated_explanation=result["translated_explanation"],
        translated_terminology=result.get("translated_terminology", []),
    )
    db.add(translation)
    db.commit()
    db.refresh(translation)
    return translation
