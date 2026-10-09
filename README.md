# MedLingo

MedLingo is an educational medical-text and prescription explainer built with React/Vite and FastAPI. It supports text entry, prescription upload/OCR, plain-language explanations, translations, per-browser history, and a safety-focused medical chat with browser voice input/output.

## Safety boundaries

- Educational information only; not diagnosis, treatment, or a substitute for a clinician or pharmacist.
- The chat does not provide personalized doses or direct users to start, stop, or change medicines.
- Urgent phrases trigger an emergency-care message; this simple keyword check is not a reliable triage system.
- OCR and AI can misread medicine names, quantities, and instructions. Verify them against the original prescription and with a qualified professional.
- Do not enter identifying patient information. The anonymous client ID is not a full authentication system.
- Not clinically validated or intended for clinical use.

## Repository layout

- `frontend/`: React, Vite, React Router.
- `backend/app/`: FastAPI routers, SQLAlchemy models, OCR and AI services.

## Local development

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# Optional: copy .env.example to .env and set ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000
```

Image OCR requires the Tesseract executable installed on the host. Without an API key, the existing analysis flow uses its offline/rule-based fallback and chat explains that AI chat is unavailable.

### Frontend

In a second terminal:

```bash
cd frontend
npm install
# Optional for local development; default API URL is http://localhost:8000/api
# PowerShell: $env:VITE_API_URL="http://localhost:8000/api"
npm run dev
```

## Render deployment

Recommended: deploy backend and frontend as separate Render services.

### 1. Backend Web Service

- Root Directory: `backend`
- Runtime: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment variables:
  - `ANTHROPIC_API_KEY`: optional secret for AI explanations, translation, and chat
  - `ANTHROPIC_MODEL`: optional; defaults to `claude-sonnet-4-6`
  - `CLIENT_ORIGIN`: exact deployed frontend URL, including `https://`
  - `DATABASE_URL`: use a persistent database URL for production; default SQLite data on an ephemeral filesystem may be lost on redeploy
  - `UPLOAD_DIR`: use a persistent disk path if uploaded files must survive restarts
- Image OCR requires Tesseract installed in the service environment. Verify OCR dependencies before relying on image uploads in production.
- After deploy, check `https://YOUR-BACKEND.onrender.com/api/health`.

### 2. Frontend Static Site

- Root Directory: `frontend`
- Build Command: `npm install && npm run build`
- Publish Directory: `dist`
- Environment variable `VITE_API_URL`: `https://YOUR-BACKEND.onrender.com/api`
- Add a rewrite rule: source `/*`, destination `/index.html`, action `Rewrite` for React Router routes.
- Set backend `CLIENT_ORIGIN` to the exact frontend URL and redeploy the backend.

## Chat and voice feature

- Chat endpoint: `POST /api/chat`, JSON body `{"message":"What does take with food mean?"}`, requires the existing `X-Client-Id` header.
- Voice input uses browser Web Speech APIs when supported; spoken replies use SpeechSynthesis. Browser and operating-system language support varies.
- Never expose the Anthropic API key in frontend environment variables; keep it only on the backend.

## Before production

Conduct a security/privacy review, configure persistent storage, review authentication and tenant isolation, verify OCR/Tesseract availability, and perform clinical safety/usability review. AI output is not medically validated.
