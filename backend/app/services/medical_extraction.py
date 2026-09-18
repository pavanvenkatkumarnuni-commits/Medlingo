import re

# A small curated reference list of common medicines with plain-language
# "commonly used for" descriptions. This is static reference data (not
# AI-generated) used so the app can still surface *something* useful when
# no AI provider is configured, and to sanity-check AI-extracted names.
# It is intentionally conservative — unknown medicines simply get no
# offline description rather than a guessed one.
KNOWN_MEDICINES = {
    "paracetamol": "A common pain reliever and fever reducer (also known as acetaminophen).",
    "acetaminophen": "A common pain reliever and fever reducer (also known as paracetamol).",
    "ibuprofen": "A nonsteroidal anti-inflammatory drug (NSAID) used for pain, inflammation and fever.",
    "amoxicillin": "A penicillin-type antibiotic used to treat a range of bacterial infections.",
    "azithromycin": "An antibiotic used to treat certain bacterial infections, including some respiratory and skin infections.",
    "metformin": "A first-line medicine for managing blood sugar in type 2 diabetes.",
    "atorvastatin": "A statin used to lower cholesterol and reduce cardiovascular risk.",
    "amlodipine": "A calcium channel blocker used to treat high blood pressure and chest pain (angina).",
    "omeprazole": "A proton pump inhibitor used to reduce stomach acid, e.g. for acid reflux or ulcers.",
    "pantoprazole": "A proton pump inhibitor used to reduce stomach acid, e.g. for acid reflux or ulcers.",
    "cetirizine": "An antihistamine used to relieve allergy symptoms such as sneezing and itching.",
    "loratadine": "An antihistamine used to relieve allergy symptoms such as sneezing and itching.",
    "aspirin": "Used at low doses to help prevent blood clots, and at higher doses for pain and fever.",
    "losartan": "An angiotensin receptor blocker (ARB) used to treat high blood pressure.",
    "metoprolol": "A beta-blocker used to treat high blood pressure and certain heart conditions.",
    "levothyroxine": "A thyroid hormone replacement used to treat an underactive thyroid (hypothyroidism).",
    "ciprofloxacin": "A fluoroquinolone antibiotic used to treat various bacterial infections.",
    "doxycycline": "A tetracycline-class antibiotic used for a range of bacterial infections.",
    "prednisone": "A corticosteroid used to reduce inflammation in a variety of conditions.",
    "prednisolone": "A corticosteroid used to reduce inflammation in a variety of conditions.",
    "salbutamol": "A bronchodilator (inhaler) used to relieve asthma or breathing difficulty symptoms.",
    "albuterol": "A bronchodilator (inhaler) used to relieve asthma or breathing difficulty symptoms.",
    "insulin": "A hormone medicine used to manage blood sugar levels in diabetes.",
    "warfarin": "A blood thinner (anticoagulant) used to prevent or treat blood clots.",
    "diazepam": "A benzodiazepine used for anxiety, muscle spasms, or seizures, under close medical supervision.",
    "ondansetron": "An anti-nausea medicine often used to prevent vomiting.",
    "clopidogrel": "An antiplatelet medicine used to help prevent blood clots.",
    "furosemide": "A diuretic ('water pill') used to reduce fluid buildup, e.g. in heart or kidney conditions.",
    "gabapentin": "Used to treat certain types of nerve pain and, in some cases, seizures.",
    "sertraline": "A selective serotonin reuptake inhibitor (SSRI) used to treat depression and anxiety disorders.",
    "metronidazole": "An antibiotic used against certain bacterial and parasitic infections.",
    "vitamin d3": "A supplement used to support bone health and correct vitamin D deficiency.",
    "folic acid": "A B-vitamin supplement, often used in pregnancy or for certain types of anemia.",
    "iron": "A mineral supplement used to treat or prevent iron-deficiency anemia.",
    "multivitamin": "A general nutritional supplement providing a mix of vitamins and minerals.",
}

DOSAGE_PATTERN = re.compile(
    r'(\d+(?:\.\d+)?\s?(?:mg|mcg|g|ml|iu|%|mg/ml|units?)\b)', re.IGNORECASE
)

FREQUENCY_PATTERNS = [
    (re.compile(r'\bonce\s+(?:a\s+day|daily)\b|\bOD\b|\bqd\b', re.IGNORECASE), "Once daily"),
    (re.compile(r'\btwice\s+(?:a\s+day|daily)\b|\bBD\b|\bBID\b', re.IGNORECASE), "Twice daily"),
    (re.compile(r'\bthree\s+times\s+(?:a\s+day|daily)\b|\bTDS\b|\bTID\b', re.IGNORECASE), "Three times daily"),
    (re.compile(r'\bfour\s+times\s+(?:a\s+day|daily)\b|\bQID\b', re.IGNORECASE), "Four times daily"),
    (re.compile(r'\bevery\s+(\d+)\s*(?:hours?|hrs?)\b', re.IGNORECASE), None),  # dynamic
    (re.compile(r'\b(\d)\s*-\s*(\d)\s*-\s*(\d)\b'), None),  # dynamic e.g. 1-0-1
    (re.compile(r'\bas\s+needed\b|\bPRN\b', re.IGNORECASE), "As needed (PRN)"),
    (re.compile(r'\bat\s+bedtime\b|\bHS\b', re.IGNORECASE), "At bedtime"),
]

DURATION_PATTERN = re.compile(
    r'\bfor\s+(\d+)\s*(day|days|week|weeks|month|months)\b|\bx\s*(\d+)\s*(day|days|week|weeks)\b',
    re.IGNORECASE
)

CONDITION_KEYWORDS = [
    "diabetes", "hypertension", "high blood pressure", "asthma", "infection",
    "fever", "cough", "cold", "allergy", "allergies", "pain", "anxiety",
    "depression", "arthritis", "migraine", "acid reflux", "gerd", "ulcer",
    "thyroid", "anemia", "cholesterol", "pneumonia", "bronchitis", "sinusitis",
    "urinary tract infection", "uti",
]

INSTRUCTION_KEYWORDS = [
    "take with food", "take on empty stomach", "avoid alcohol", "do not crush",
    "complete the full course", "store in a cool place", "avoid sunlight",
    "take with plenty of water", "do not stop suddenly", "avoid driving",
    "take before meals", "take after meals", "shake well before use",
]

STOPWORDS_NEAR_CAPS = {
    "Take", "Tablet", "Tablets", "Capsule", "Capsules", "Dosage", "Dose",
    "Morning", "Evening", "Night", "Daily", "Please", "Note", "Rx", "Dr",
}


def _extract_frequency(text: str) -> str | None:
    for pattern, label in FREQUENCY_PATTERNS:
        m = pattern.search(text)
        if m:
            if label:
                return label
            if pattern.pattern.startswith(r'\bevery'):
                return f"Every {m.group(1)} hours"
            if '-' in pattern.pattern:
                return f"{m.group(1)}-{m.group(2)}-{m.group(3)} (morning-afternoon-night)"
    return None


def _extract_duration(text: str) -> str | None:
    m = DURATION_PATTERN.search(text)
    if not m:
        return None
    if m.group(1):
        return f"{m.group(1)} {m.group(2)}"
    return f"{m.group(3)} {m.group(4)}"


WINDOW_CHARS = 90  # how far past a medicine name we look for its own dosage/frequency/duration


def _find_medicine_occurrences(text: str) -> list[tuple[str, int]]:
    """Return [(display_name, start_index)] for every medicine mention, in
    order of appearance, so each occurrence can later be matched with the
    dosage/frequency/duration that appears *near it* rather than anywhere
    in the whole document."""
    occurrences = []
    lower = text.lower()

    for name in KNOWN_MEDICINES:
        for m in re.finditer(rf'\b{re.escape(name)}\b', lower):
            occurrences.append((name.title(), m.start()))

    for m in re.finditer(r'\b([A-Z][a-zA-Z]{2,})\s+(?=\d+(?:\.\d+)?\s?(?:mg|mcg|g|ml|iu)\b)', text):
        word = m.group(1)
        if word not in STOPWORDS_NEAR_CAPS and word.lower() not in KNOWN_MEDICINES:
            occurrences.append((word.title(), m.start()))

    occurrences.sort(key=lambda x: x[1])

    # De-duplicate the same medicine name mentioned multiple times close
    # together (keep the first occurrence, which is usually the one with
    # its dosage attached in a prescription line).
    seen = set()
    deduped = []
    for name, pos in occurrences:
        if name in seen:
            continue
        seen.add(name)
        deduped.append((name, pos))
    return deduped


def extract_structured_fields(text: str) -> dict:
    """
    Deterministic, regex/lookup based extraction. Used as the offline
    fallback and to sanity-check AI output. Returns only what it can
    actually find in the text — never guesses values it has no pattern
    match for, and associates dosage/frequency/duration with the medicine
    they actually appear next to rather than applying the first match in
    the document to every medicine found.
    """
    occurrences = _find_medicine_occurrences(text)
    conditions = sorted({kw for kw in CONDITION_KEYWORDS if kw in text.lower()})
    instructions = sorted({kw.capitalize() for kw in INSTRUCTION_KEYWORDS if kw in text.lower()})

    medicines = []
    for name, pos in occurrences:
        window = text[pos:pos + WINDOW_CHARS]
        dosage_match = DOSAGE_PATTERN.search(window)
        frequency = _extract_frequency(window)
        duration = _extract_duration(window)
        known = KNOWN_MEDICINES.get(name.lower())

        medicines.append({
            "name": name,
            "dosage": dosage_match.group(1) if dosage_match else None,
            "frequency": frequency,
            "duration": duration,
            "instructions": ", ".join(instructions) if instructions else None,
            "common_use": known,
            "plain_explanation": None,
            "confidence": "medium" if known else "low",
        })

    warnings = []
    if not medicines:
        warnings.append("No medicine names could be confidently identified from this text.")
    else:
        if any(m["dosage"] is None for m in medicines):
            warnings.append("Dosage could not be confidently identified for one or more medicines.")
        if any(m["frequency"] is None for m in medicines):
            warnings.append("Dosing frequency could not be confidently identified for one or more medicines.")

    return {
        "medicines": medicines,
        "conditions": conditions,
        "instructions": instructions,
        "warnings": warnings,
    }
