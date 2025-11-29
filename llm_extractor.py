# llm_extractor.py

import json
from typing import List, Dict, Tuple
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set in environment or .env")

client = OpenAI(api_key=OPENAI_API_KEY)


ALLOWED_PAGE_TYPES = {"bill detail", "final bill", "pharmacy"}


def normalize_page_type(raw: str) -> str:
    if not raw:
        return "Bill Detail"

    s = raw.strip().lower()
    for pt in ALLOWED_PAGE_TYPES:
        if pt in s:
            # return in title case as per spec
            return " ".join(word.capitalize() for word in pt.split())

    return "Bill Detail"


def safe_float(val, default: float = 0.0) -> float:
    try:
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            val = val.replace(",", "").strip()
            if not val:
                return default
            return float(val)
    except Exception:
        return default
    return default


def extract_page_with_llm(page_no: int, page_text: str) -> Tuple[str, List[Dict], int, int, int]:
    """
    Send OCR'ed page text to LLM and get:
      - page_type (Bill Detail | Final Bill | Pharmacy)
      - items: list of {item_name, item_quantity, item_rate, item_amount}
    Returns: (page_type, items, input_tokens, output_tokens, total_tokens)
    """
    if not page_text or not page_text.strip():
        return "Bill Detail", [], 0, 0, 0

    system_prompt = (
        "You are an expert system for extracting line items from medical bills and invoices. "
        "You will be given OCR text from a single page.\n"
        "Your job is to:\n"
        "1. Identify all billable line items (treatments, tests, medicines, services, etc.).\n"
        "2. Exclude summary lines like Sub-total, Total, Grand Total, GST, discounts, taxes.\n"
        "3. For each item, extract:\n"
        "   - item_name (as appears in the bill, but you may normalize minor OCR errors)\n"
        "   - item_quantity (if not explicitly written, infer 1 if obviously a single item; otherwise 0)\n"
        "   - item_rate (per-unit rate if available; otherwise 0)\n"
        "   - item_amount (net amount after discounts as per bill)\n"
        "4. Identify the page type: one of 'Bill Detail', 'Final Bill', or 'Pharmacy'.\n"
        "   Use 'Pharmacy' if this page is clearly a medicine / drug / pharmacy bill. "
        "   Use 'Final Bill' if this looks like a final summary of all charges. "
        "   Otherwise use 'Bill Detail'.\n"
        "Return STRICT JSON with keys: page_type, items.\n"
        "DO NOT include any explanation or extra keys.\n"
    )

    user_prompt = (
        f"PAGE_NO: {page_no}\n"
        "OCR_TEXT:\n"
        "-------------------\n"
        f"{page_text}\n"
        "-------------------\n\n"
        "Respond in this JSON format:\n"
        "{\n"
        '  \"page_type\": \"Bill Detail | Final Bill | Pharmacy\",\n'
        "  \"items\": [\n"
        "    {\n"
        "      \"item_name\": \"string\",\n"
        "      \"item_quantity\": number,\n"
        "      \"item_rate\": number,\n"
        "      \"item_amount\": number\n"
        "    }\n"
        "  ]\n"
        "}\n"
    )

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.1,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    usage = getattr(resp, "usage", None)
    input_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
    output_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
    total_tokens = getattr(usage, "total_tokens", 0) if usage else (input_tokens + output_tokens)

    content = resp.choices[0].message.content
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # If LLM still misbehaves, return empty items
        return "Bill Detail", [], input_tokens, output_tokens, total_tokens

    raw_page_type = data.get("page_type", "Bill Detail")
    page_type = normalize_page_type(raw_page_type)

    items_raw = data.get("items", []) or []
    items: List[Dict] = []

    for it in items_raw:
        name = (it.get("item_name") or "").strip()
        if not name:
            continue

        qty = safe_float(it.get("item_quantity"), 0.0)
        rate = safe_float(it.get("item_rate"), 0.0)
        amount = safe_float(it.get("item_amount"), 0.0)

        items.append(
            {
                "item_name": name,
                "item_quantity": qty,
                "item_rate": rate,
                "item_amount": amount,
            }
        )

    return page_type, items, input_tokens, output_tokens, total_tokens
