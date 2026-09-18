import pytesseract
from PIL import Image
import pdfplumber
from app.config import settings

pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


class ExtractionError(Exception):
    pass


def extract_text_from_image(file_path: str) -> str:
    try:
        image = Image.open(file_path)
        # Basic preprocessing: convert to greyscale, which measurably helps
        # OCR accuracy on photographed/scanned prescriptions.
        image = image.convert("L")
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        raise ExtractionError(f"Could not read text from this image: {e}")


def extract_text_from_pdf(file_path: str) -> str:
    try:
        chunks = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                chunks.append(page_text)
        text = "\n".join(chunks).strip()
        if not text:
            raise ExtractionError(
                "No selectable text found in this PDF. It may be a scanned "
                "image PDF — try uploading it as a JPG/PNG instead so OCR can read it."
            )
        return text
    except ExtractionError:
        raise
    except Exception as e:
        raise ExtractionError(f"Could not read text from this PDF: {e}")


def extract_text(file_path: str, file_type: str) -> str:
    if file_type in ("image/jpeg", "image/png", "image/jpg"):
        return extract_text_from_image(file_path)
    if file_type == "application/pdf":
        return extract_text_from_pdf(file_path)
    raise ExtractionError(f"Unsupported file type: {file_type}")
