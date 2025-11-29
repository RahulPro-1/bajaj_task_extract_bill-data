# ocr_utils.py

import io
from typing import List, Tuple
import requests
import pdfplumber
from PIL import Image
import pytesseract
from config import TESSERACT_CMD

# Configure tesseract path if provided
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def download_document(url: str) -> Tuple[io.BytesIO, str]:
    """
    Download the remote document and guess its type.
    Returns (file_bytes_io, file_type) where file_type is 'pdf' or 'image'.
    """
    resp = requests.get(url, timeout=40)
    resp.raise_for_status()

    content_type = (resp.headers.get("Content-Type") or "").lower()
    file_bytes = io.BytesIO(resp.content)

    # Prefer header-based detection, then extension
    if "pdf" in content_type or url.lower().endswith(".pdf"):
        return file_bytes, "pdf"

    # Basic image types
    if any(ext in url.lower() for ext in [".png", ".jpg", ".jpeg", ".tif", ".tiff"]):
        return file_bytes, "image"

    # Fallback: if header says image
    if "image" in content_type:
        return file_bytes, "image"

    # Final fallback: try pdf first, then image at call-site if needed
    return file_bytes, "pdf"


def extract_pages_text(file_bytes: io.BytesIO, file_type: str) -> List[str]:
    """
    Returns a list of raw text for each page (joined string per page).
    """
    if file_type == "pdf":
        return _extract_pdf_pages_text(file_bytes)

    # If not PDF, assume single-page image
    return _extract_image_pages_text(file_bytes)


def _extract_pdf_pages_text(file_bytes: io.BytesIO) -> List[str]:
    """
    Extract text from each PDF page.
    If the PDF has no text layer (scanned PDF), apply OCR.
    """
    pages_text: List[str] = []

    with pdfplumber.open(file_bytes) as pdf:
        for page in pdf.pages:
            # 1. Try normal text extraction
            text = page.extract_text()
            if text and text.strip():
                pages_text.append(text)
                continue

            # 2. Fallback: OCR on rendered image
            pil_image = page.to_image(resolution=300).original
            ocr_text = pytesseract.image_to_string(pil_image)
            pages_text.append(ocr_text or "")

    return pages_text


def _extract_image_pages_text(file_bytes: io.BytesIO) -> List[str]:
    """
    Extract text from image files (PNG/JPG).
    """
    image = Image.open(file_bytes)
    text = pytesseract.image_to_string(image)
    return [text or ""]
