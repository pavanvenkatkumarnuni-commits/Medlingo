import json
import httpx
from abc import ABC, abstractmethod
from app.config import settings
from app.schemas import SUPPORTED_LANGUAGES

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

ANALYSIS_SYSTEM_PROMPT = """You are a careful medical-information assistant helping a layperson \
understand a prescription or medical text. You are NOT a doctor and must never present your \
output as a diagnosis or a definitive medical instruction.

Rules you must follow strictly:
- Only report medicines, dosages, frequencies, durations, and conditions that are actually \
present in the given text, or are extremely well-established knowledge about a medicine that \
IS named in the text (e.g. what a named medicine is commonly used for). Never invent a \
medicine, dosage, or condition that is not supported by the text.
- If something is unclear, ambiguous, or missing, say so plainly in a "warnings" entry instead \
of guessing.
- Use short, plain, non-technical language a patient without medical training can understand.
- Respond with ONLY a single JSON object, no prose before or after, matching exactly this shape:
{
  "medicines": [
    {"name": str, "dosage": str|null, "frequency": str|null, "duration": str|null,
     "instructions": str|null, "common_use": str, "plain_explanation": str, "confidence": "high"|"medium"|"low"}
  ],
  "conditions": [str],
  "instructions": [str],
  "explanation_text": str,
  "terminology": [{"term": str, "meaning": str}],
  "warnings": [str]
}
"explanation_text" should be a short, warm, plain-language summary (3-6 sentences) of what this \
means for the patient overall. "terminology" should explain any medical jargon that appears in \
the text (max 8 terms)."""

TRANSLATE_SYSTEM_PROMPT = """You translate patient-facing medical explanations into the requested \
language. Keep medicine (brand/generic drug) names and numeric dosage figures (e.g. "500mg", \
"twice daily", "5 days") unchanged/untranslated unless a translation is clearly more natural and \
unambiguous for a patient reading in that language — never alter the actual numbers or units. \
Respond with ONLY a single JSON object of this shape, no prose:
{"translated_explanation": str, "translated_terminology": [{"term": str, "meaning": str}]}"""


class AIProviderError(Exception):
    pass


class AIProvider(ABC):
    name = "base"

    @abstractmethod
    def analyze(self, raw_text: str, rule_based: dict) -> dict:
        ...

    @abstractmethod
    def translate(self, explanation_text: str, terminology: list, target_language_code: str) -> dict:
        ...


class OfflineProvider(AIProvider):
    """
    Honest fallback used when no AI provider is configured. It never
    fabricates medical explanations — it only reformats what the
    deterministic rule-based extractor already found, and clearly labels
    anything it cannot provide.
    """
    name = "offline"

    def analyze(self, raw_text: str, rule_based: dict) -> dict:
        medicines = []
        for m in rule_based["medicines"]:
            plain = (
                m["common_use"]
                or "No reference explanation is available for this medicine offline. "
                   "Configure an AI provider (see .env) for a full plain-language explanation."
            )
            medicines.append({**m, "plain_explanation": plain})

        if medicines:
            names = ", ".join(m["name"] for m in medicines)
            explanation = (
                f"We identified the following in your text: {names}. "
                "This offline summary only reformats patterns we could detect automatically "
                "(medicine names, dosage, frequency, duration) — it is not an AI-generated "
                "explanation. Configure an AI provider for a fuller, more reliable explanation."
            )
        else:
            explanation = (
                "We could not confidently identify any medicine names, dosages, or "
                "instructions in this text using offline pattern matching. Configure an AI "
                "provider for a more capable explanation, or try providing clearer text."
            )

        warnings = list(rule_based["warnings"])
        warnings.append("AI provider is not configured — this is a rule-based summary only, not an AI-generated explanation.")

        return {
            "medicines": medicines,
            "conditions": rule_based["conditions"],
            "instructions": rule_based["instructions"],
            "explanation_text": explanation,
            "terminology": [],
            "warnings": warnings,
            "provider_used": "offline",
        }

    def translate(self, explanation_text: str, terminology: list, target_language_code: str) -> dict:
        lang_name = SUPPORTED_LANGUAGES.get(target_language_code, target_language_code)
        return {
            "translated_explanation": (
                f"Translation to {lang_name} is unavailable because no AI provider is "
                f"configured. Set ANTHROPIC_API_KEY in the backend .env file to enable "
                f"translation. Original (English) explanation:\n\n{explanation_text}"
            ),
            "translated_terminology": terminology,
        }


class AnthropicProvider(AIProvider):
    name = "anthropic"

    def __init__(self):
        if not settings.anthropic_api_key:
            raise AIProviderError("ANTHROPIC_API_KEY is not configured")
        self._client = httpx.Client(
            base_url="https://api.anthropic.com",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            timeout=45.0,
        )

    def _call(self, system: str, user: str) -> dict:
        try:
            resp = self._client.post("/v1/messages", json={
                "model": settings.anthropic_model,
                "max_tokens": 1500,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            })
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise AIProviderError(f"Anthropic API error ({e.response.status_code}): {e.response.text[:300]}")
        except httpx.HTTPError as e:
            raise AIProviderError(f"Could not reach Anthropic API: {e}")

        data = resp.json()
        text_blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
        raw = "\n".join(text_blocks).strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise AIProviderError("AI provider returned a response that could not be parsed as JSON")

    def analyze(self, raw_text: str, rule_based: dict) -> dict:
        user_prompt = (
            f"Here is the medical text to analyze:\n\n\"\"\"\n{raw_text}\n\"\"\"\n\n"
            f"For reference, deterministic pattern matching already found these candidate "
            f"medicine names (verify, don't blindly trust): {[m['name'] for m in rule_based['medicines']] or 'none'}."
        )
        result = self._call(ANALYSIS_SYSTEM_PROMPT, user_prompt)
        result["provider_used"] = "anthropic"
        result.setdefault("medicines", [])
        result.setdefault("conditions", [])
        result.setdefault("instructions", [])
        result.setdefault("terminology", [])
        result.setdefault("warnings", [])
        for m in result["medicines"]:
            m.setdefault("confidence", "medium")
        return result

    def translate(self, explanation_text: str, terminology: list, target_language_code: str) -> dict:
        lang_name = SUPPORTED_LANGUAGES.get(target_language_code, target_language_code)
        user_prompt = (
            f"Target language: {lang_name}\n\n"
            f"Explanation to translate:\n{explanation_text}\n\n"
            f"Terminology list to translate (keep the same JSON array shape):\n{json.dumps(terminology)}"
        )
        result = self._call(TRANSLATE_SYSTEM_PROMPT, user_prompt)
        result.setdefault("translated_terminology", terminology)
        return result


def get_provider() -> AIProvider:
    if settings.ai_provider == "anthropic" and settings.anthropic_api_key:
        try:
            return AnthropicProvider()
        except AIProviderError:
            return OfflineProvider()
    return OfflineProvider()
