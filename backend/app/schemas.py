from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

SUPPORTED_LANGUAGES = {
    "en": "English", "te": "Telugu", "hi": "Hindi", "ta": "Tamil",
    "kn": "Kannada", "ml": "Malayalam", "bn": "Bengali", "mr": "Marathi",
    "gu": "Gujarati", "pa": "Punjabi", "ur": "Urdu", "es": "Spanish",
    "fr": "French", "ar": "Arabic", "zh": "Chinese (Simplified)",
}


class TextAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=8000)
    language: str = "en"

    @field_validator("text")
    @classmethod
    def not_blank(cls, v):
        if not v.strip():
            raise ValueError("Text cannot be blank")
        return v.strip()

    @field_validator("language")
    @classmethod
    def valid_language(cls, v):
        if v not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language code: {v}")
        return v


class DocumentAnalyzeRequest(BaseModel):
    language: str = "en"

    @field_validator("language")
    @classmethod
    def valid_language(cls, v):
        if v not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language code: {v}")
        return v


class TranslateRequest(BaseModel):
    language: str

    @field_validator("language")
    @classmethod
    def valid_language(cls, v):
        if v not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language code: {v}")
        return v


class MedicineOut(BaseModel):
    id: str
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None
    common_use: Optional[str] = None
    plain_explanation: Optional[str] = None
    confidence: str

    class Config:
        from_attributes = True


class TranslationOut(BaseModel):
    language: str
    translated_explanation: str
    translated_terminology: list = []

    class Config:
        from_attributes = True


class DocumentOut(BaseModel):
    id: str
    filename: str
    file_type: str
    status: str
    raw_text: Optional[str] = None
    extraction_error: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class AnalysisOut(BaseModel):
    id: str
    source_type: str
    source_label: Optional[str] = None
    raw_text: str
    conditions: List[str] = []
    instructions: List[str] = []
    explanation_text: Optional[str] = None
    terminology: List[dict] = []
    warnings: List[str] = []
    ai_provider_used: str
    language: str
    created_at: datetime
    medicines: List[MedicineOut] = []
    translations: List[TranslationOut] = []

    class Config:
        from_attributes = True


class AnalysisSummaryOut(BaseModel):
    id: str
    source_type: str
    source_label: Optional[str] = None
    medicine_names: List[str] = []
    language: str
    created_at: datetime

    class Config:
        from_attributes = True
