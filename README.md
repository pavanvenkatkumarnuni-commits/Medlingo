# MedLingo AI — AI Medical Translator

Understand your medical information in simple language. Upload a prescription or paste medical
text, and MedLingo AI extracts the medicines, dosages and instructions, explains them in plain
language, and translates the explanation into your language.

> ⚠️ **For informational purposes only.** MedLingo AI does not replace advice, diagnosis, or
> treatment from a qualified healthcare professional.

## Stack

- **Frontend:** React (Vite), React Router, Axios
- **Backend:** Python, FastAPI, SQLAlchemy, SQLite
- **OCR:** Tesseract (via `pytesseract`) for images, `pdfplumber` for PDFs
- **AI:** Anthropic API (configurable via env var) for medical explanation + translation, with an
  honest rule-based offline fallback that never invents information when no AI key is configured

## Project structure

```
medlingo/
  backend/            FastAPI app
    app/
      main.py          App entrypoint, CORS, routes
      config.py         Env-based settings
      database.py        SQLAlchemy engine/session
      models.py           ORM models (users, documents, analysis_results, medicines, translations)
      schemas.py            Pydantic request/response schemas
      deps.py                 Anonymous client-id user resolution
      routers/
        documents.py    Upload + OCR/PDF extraction
        analyze.py        Text/document analysis pipeline
        translate.py        Translation endpoint
        history.py             History list/get/delete
      services/
        extraction.py    OCR (images) / text extraction (PDFs)
        medical_extraction.py  Deterministic regex-based medicine/dosage/frequency/duration extraction
        ai_provider.py    Anthropic integration + offline fallback provider
    requirements.txt
    .env.example
  frontend/           React (Vite) app
    src/
      api/client.js     Axios instance + anonymous client-id header
      components/         Navbar, SafetyBanner, LanguageSelector
      pages/
        Home.jsx           Landing/dashboard
        UploadPrescription.jsx  Drag-and-drop upload + OCR analysis
        TextAnalyzer.jsx          Paste-text analysis
        Results.jsx                 Explanation, medicines, terminology, translation
        History.jsx                   Past analyses
    .env.example
```

## Setup

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — at minimum set ANTHROPIC_API_KEY if you want real AI explanations
# and translations. Without it, the app still runs and performs rule-based
# extraction, but will say so honestly instead of inventing explanations.

# Tesseract OCR must be installed on your system for image uploads to work:
#   macOS:   brew install tesseract
#   Ubuntu:  sudo apt-get install tesseract-ocr
#   Windows: https://github.com/UB-Mannheim/tesseract/wiki

uvicorn app.main:app --reload --port 8000
```

The API is now running at `http://localhost:8000`. Interactive docs: `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env   # defaults to http://localhost:8000/api, adjust if needed
npm run dev
```

Open `http://localhost:5173`.

## How identity works

MedLingo doesn't require sign-up. On first visit, the frontend generates a random client id and
stores it in `localStorage`, sending it as the `X-Client-Id` header on every request. The backend
uses this to scope documents and history per browser/device. This keeps the app fully functional
without an authentication system the spec didn't call for, while still giving each "user" their
own persistent history in the database.

## AI provider configuration

Set these in `backend/.env`:

```
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-6
```

With no key configured, `AI_PROVIDER` falls back to an offline mode automatically. In offline
mode:
- Medicine names, dosage, frequency, duration, conditions and instructions are still extracted
  using deterministic pattern matching (regex + a small reference list of common medicines).
- Explanations are limited to that reference data — the app clearly states when it can't provide
  a fuller AI-generated explanation, rather than fabricating one.
- Translation requests return a clear notice that translation requires an AI provider, instead of
  producing a fake translation.

This is intentional: **the app should never present invented medical information as fact.**

## API overview

| Method | Endpoint                         | Purpose                                  |
|--------|-----------------------------------|-------------------------------------------|
| POST   | `/api/documents/upload`           | Upload a prescription file (JPG/PNG/PDF), runs OCR/text extraction |
| POST   | `/api/analyze/text`               | Analyze pasted medical text |
| POST   | `/api/analyze/document/{id}`      | Analyze a previously uploaded document |
| GET    | `/api/analyze/{id}`               | Fetch a single analysis |
| POST   | `/api/translate/{id}`             | Translate an analysis's explanation into a target language |
| GET    | `/api/history`                    | List past analyses for the current browser |
| GET    | `/api/history/{id}`               | Fetch one past analysis in full |
| DELETE | `/api/history/{id}`               | Delete a past analysis |
| GET    | `/api/health`                     | Health check + whether an AI provider is configured |

## Notes on accuracy

OCR and rule-based extraction are inherently imperfect on messy handwriting or unusual formatting.
The app is designed to be honest about this: medicines are labeled with a confidence level, and
whenever something can't be confidently identified, that's stated explicitly as a warning rather
than filled in with a guess.
