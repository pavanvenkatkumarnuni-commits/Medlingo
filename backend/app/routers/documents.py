import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app import models, schemas
from app.config import settings
from app.services.extraction import extract_text, ExtractionError

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/jpg", "application/pdf"}


@router.post("/upload", response_model=schemas.DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPG, PNG, and PDF files are supported.")

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(contents) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File is too large. Maximum allowed size is {settings.max_upload_size_mb}MB.",
        )

    ext = os.path.splitext(file.filename or "")[1] or ""
    stored_name = f"{uuid.uuid4()}{ext}"
    stored_path = os.path.join(settings.upload_dir, stored_name)
    with open(stored_path, "wb") as f:
        f.write(contents)

    doc = models.Document(
        user_id=user.id,
        filename=file.filename or stored_name,
        file_type=file.content_type,
        file_path=stored_path,
        file_size_bytes=len(contents),
        status="uploaded",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Extract text synchronously (OCR/PDF parsing). For very large files a
    # real production system would push this to a background worker/queue;
    # kept synchronous here for simplicity and because it's fast enough for
    # single prescription images/PDFs.
    try:
        text = extract_text(doc.file_path, doc.file_type)
        doc.raw_text = text
        doc.status = "extracted"
    except ExtractionError as e:
        doc.status = "failed"
        doc.extraction_error = str(e)

    db.commit()
    db.refresh(doc)
    return doc


@router.get("/{document_id}", response_model=schemas.DocumentOut)
def get_document(document_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    doc = db.query(models.Document).filter(models.Document.id == document_id, models.Document.user_id == user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc
