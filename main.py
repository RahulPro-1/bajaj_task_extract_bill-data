# main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles   # 🔹 Added

from models import (
    ExtractRequest,
    ExtractResponse,
    TokenUsage,
    ExtractResponseData,
    PageLineItems,
    BillItem,
)
from ocr_utils import download_document, extract_pages_text
from llm_extractor import extract_page_with_llm


app = FastAPI(
    title="HackRx Bill Extraction API",
    description="LLM-powered bill line item extractor",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 ADD STATIC FILE HOSTING HERE
# -------------------------------
# This makes /static/<filename> accessible publicly
# Make sure you create a folder named "static" in your project root.
app.mount("/static", StaticFiles(directory="static"), name="static")
# -------------------------------


@app.post("/extract-bill-data", response_model=ExtractResponse)
def extract_bill_data(request: ExtractRequest) -> ExtractResponse:
    try:
        # 1. Download file
        file_bytes, file_type = download_document(str(request.document))

        # 2. OCR / text extraction page-wise
        pages_text = extract_pages_text(file_bytes, file_type)

        pagewise_line_items = []
        total_item_count = 0

        cumulative_total_tokens = 0
        cumulative_input_tokens = 0
        cumulative_output_tokens = 0

        # 3. For each page, use LLM to extract items
        for idx, page_text in enumerate(pages_text, start=1):
            page_type, items_raw, in_tok, out_tok, tot_tok = extract_page_with_llm(idx, page_text)

            cumulative_input_tokens += in_tok
            cumulative_output_tokens += out_tok
            cumulative_total_tokens += tot_tok

            bill_items = [
                BillItem(
                    item_name=it["item_name"],
                    item_amount=float(it["item_amount"]),
                    item_rate=float(it["item_rate"]),
                    item_quantity=float(it["item_quantity"]),
                )
                for it in items_raw
            ]

            total_item_count += len(bill_items)

            pagewise_line_items.append(
                PageLineItems(
                    page_no=str(idx),
                    page_type=page_type,
                    bill_items=bill_items,
                )
            )

        token_usage = TokenUsage(
            total_tokens=cumulative_total_tokens,
            input_tokens=cumulative_input_tokens,
            output_tokens=cumulative_output_tokens,
        )

        data = ExtractResponseData(
            pagewise_line_items=pagewise_line_items,
            total_item_count=total_item_count,
        )

        return ExtractResponse(
            is_success=True,
            token_usage=token_usage,
            data=data,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
