# config.py

import os
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # must be set
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

# Optional: explicitly set tesseract path via env
TESSERACT_CMD = os.getenv("TESSERACT_CMD")  # e.g. C:\Program Files\Tesseract-OCR\tesseract.exe
