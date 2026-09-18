import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from app.database import Base


def gen_id():
    return str(uuid.uuid4())


class User(Base):
    """
    Lightweight, auth-free user record. MedLingo does not require sign-up —
    the frontend generates a persistent anonymous client id (stored in
    localStorage) on first visit and sends it as the X-Client-Id header.
    This lets history/documents be scoped per-browser without forcing an
    account system the spec didn't ask for.
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_id)
    display_name = Column(String, nullable=True)
    preferred_language = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    analyses = relationship("AnalysisResult", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # image/jpeg, image/png, application/pdf
    file_path = Column(String, nullable=False)
    file_size_bytes = Column(Integer, default=0)
    status = Column(String, default="uploaded")  # uploaded, extracted, failed
    raw_text = Column(Text, nullable=True)
    extraction_error = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="documents")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)

    source_type = Column(String, nullable=False)  # "upload" | "text"
    source_label = Column(String, nullable=True)  # filename or a short snippet of pasted text
    raw_text = Column(Text, nullable=False)

    conditions = Column(JSON, default=list)          # list[str]
    instructions = Column(JSON, default=list)        # list[str] general instructions not tied to one medicine
    explanation_text = Column(Text, nullable=True)    # AI (or fallback) plain-language explanation
    terminology = Column(JSON, default=list)          # list[{term, meaning}]
    warnings = Column(JSON, default=list)             # list[str] — uncertainty / low-confidence notices
    ai_provider_used = Column(String, default="none") # "anthropic" | "offline" | "none"

    language = Column(String, default="en")           # language the explanation is currently shown in
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="analyses")
    medicines = relationship("Medicine", back_populates="analysis", cascade="all, delete-orphan")
    translations = relationship("Translation", back_populates="analysis", cascade="all, delete-orphan")


class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(String, primary_key=True, default=gen_id)
    analysis_id = Column(String, ForeignKey("analysis_results.id"), nullable=False)

    name = Column(String, nullable=False)
    dosage = Column(String, nullable=True)
    frequency = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    instructions = Column(Text, nullable=True)
    common_use = Column(Text, nullable=True)          # what it's commonly used for
    plain_explanation = Column(Text, nullable=True)   # simple-language explanation for this medicine
    confidence = Column(String, default="medium")     # "high" | "medium" | "low"

    analysis = relationship("AnalysisResult", back_populates="medicines")


class Translation(Base):
    __tablename__ = "translations"

    id = Column(String, primary_key=True, default=gen_id)
    analysis_id = Column(String, ForeignKey("analysis_results.id"), nullable=False)
    language = Column(String, nullable=False)
    translated_explanation = Column(Text, nullable=False)
    translated_terminology = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    analysis = relationship("AnalysisResult", back_populates="translations")
