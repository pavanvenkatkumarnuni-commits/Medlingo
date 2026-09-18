from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app import models, schemas
from app.services.medical_extraction import extract_structured_fields
from app.services.ai_provider import get_provider, AIProviderError

router = APIRouter(prefix="/api/analyze", tags=["analyze"])


def _run_pipeline(db: Session, user: models.User, raw_text: str, language: str,
                   source_type: str, source_label: str, document_id: str | None) -> models.AnalysisResult:
    rule_based = extract_structured_fields(raw_text)
    provider = get_provider()

    try:
        result = provider.analyze(raw_text, rule_based)
    except AIProviderError as e:
        # Never crash the request or invent data — fall back to the honest
        # offline summary and surface the underlying error as a warning.
        from app.services.ai_provider import OfflineProvider
        result = OfflineProvider().analyze(raw_text, rule_based)
        result["warnings"] = [f"AI provider error: {e}"] + result["warnings"]

    analysis = models.AnalysisResult(
        user_id=user.id,
        document_id=document_id,
        source_type=source_type,
        source_label=source_label[:120] if source_label else None,
        raw_text=raw_text,
        conditions=result.get("conditions", []),
        instructions=result.get("instructions", []),
        explanation_text=result.get("explanation_text"),
        terminology=result.get("terminology", []),
        warnings=result.get("warnings", []),
        ai_provider_used=result.get("provider_used", "offline"),
        language=language if result.get("provider_used") == "anthropic" or language == "en" else "en",
    )
    db.add(analysis)
    db.flush()

    for m in result.get("medicines", []):
        db.add(models.Medicine(
            analysis_id=analysis.id,
            name=m.get("name", "Unknown"),
            dosage=m.get("dosage"),
            frequency=m.get("frequency"),
            duration=m.get("duration"),
            instructions=m.get("instructions"),
            common_use=m.get("common_use"),
            plain_explanation=m.get("plain_explanation"),
            confidence=m.get("confidence", "medium"),
        ))

    # If the user asked for a non-English explanation up front and we have a
    # capable provider, translate immediately so the first view is already
    # in their language; otherwise leave it in English with a clear note
    # (handled by the offline provider's translate()).
    if language != "en":
        try:
            t = provider.translate(analysis.explanation_text or "", analysis.terminology or [], language)
            db.add(models.Translation(
                analysis_id=analysis.id,
                language=language,
                translated_explanation=t["translated_explanation"],
                translated_terminology=t.get("translated_terminology", []),
            ))
        except AIProviderError as e:
            db.add(models.Translation(
                analysis_id=analysis.id,
                language=language,
                translated_explanation=f"Translation failed: {e}",
                translated_terminology=[],
            ))

    db.commit()
    db.refresh(analysis)
    return analysis


@router.post("/text", response_model=schemas.AnalysisOut)
def analyze_text(
    payload: schemas.TextAnalyzeRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    label = payload.text[:60] + ("…" if len(payload.text) > 60 else "")
    analysis = _run_pipeline(db, user, payload.text, payload.language, "text", label, None)
    return analysis


@router.post("/document/{document_id}", response_model=schemas.AnalysisOut)
def analyze_document(
    document_id: str,
    payload: schemas.DocumentAnalyzeRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    doc = db.query(models.Document).filter(models.Document.id == document_id, models.Document.user_id == user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != "extracted" or not doc.raw_text:
        raise HTTPException(
            status_code=400,
            detail=doc.extraction_error or "This document has no extracted text to analyze yet.",
        )

    analysis = _run_pipeline(db, user, doc.raw_text, payload.language, "upload", doc.filename, doc.id)
    return analysis


@router.get("/{analysis_id}", response_model=schemas.AnalysisOut)
def get_analysis(analysis_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    analysis = db.query(models.AnalysisResult).filter(
        models.AnalysisResult.id == analysis_id, models.AnalysisResult.user_id == user.id
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis
