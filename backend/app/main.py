from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import Base, engine
from app import models
from app.routers import documents, analyze, translate, history
from app.services.ai_provider import AIProviderError

Base.metadata.create_all(bind=engine)

app = FastAPI(title="MedLingo AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.client_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(AIProviderError)
def handle_ai_provider_error(request: Request, exc: AIProviderError):
    return JSONResponse(status_code=502, content={"detail": str(exc)})

@app.get("/api/health")
def health():
    return {"status": "ok", "ai_provider_configured": bool(settings.anthropic_api_key)}

app.include_router(documents.router)
app.include_router(analyze.router)
app.include_router(translate.router)
app.include_router(history.router)
