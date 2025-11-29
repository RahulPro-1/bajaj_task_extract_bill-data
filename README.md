# 📘 HackRx Bill Extraction API (OCR + LLM)

A production-ready API for extracting line items, subtotals, and totals from medical/pharmacy bills using **OCR + LLM reasoning**, built to match the **HackRx Datathon specification**.

This solution handles:
- multi-page bills  
- scanned PDFs  
- noisy OCR text  
- pharmacy invoices  
- final summary pages  
- complex billing tables  

Accuracy is improved using **LLM-based extraction** instead of regex-only parsing.

---

# 🚀 Features

- 🔍 **OCR Support**  
  - Text PDFs  
  - Scanned PDFs  
  - PNG/JPG images  
  - Automatic OCR fallback when no text layer exists  

- 🧠 **LLM-Powered Extraction**  
  Uses OpenAI GPT-4.1 (or any GPT-4+ compatible model) to:
  - detect line items  
  - infer quantities/rates  
  - ignore totals/GST  
  - classify page type  

- 📄 **Page-Level Extraction**  
  Output matches EXACT HackRx format:
  - `page_no`  
  - `page_type`  
  - `bill_items`  
  - `total_item_count`  
  - `token_usage`  

- 🔗 **Supports Any Public URL**  
  Works with PDFs and images hosted on:
  - GitHub Raw  
  - S3  
  - Transfer.sh  
  - Local servers  
  - Any direct file URL  

---

# 📂 Project Structure

```
bajaj_bill_extractor/
│
├── main.py
├── models.py
├── ocr_utils.py
├── llm_extractor.py
├── config.py
├── requirements.txt
└── README.md
```

---

# 🔧 Installation

## 1️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

## 2️⃣ Install Tesseract OCR (required for scanned PDFs)

### Windows (recommended UB Mannheim build):
https://github.com/UB-Mannheim/tesseract/wiki

Default installation path:

```
C:\Program Files\Tesseract-OCR	esseract.exe
```

---

## 3️⃣ Create `.env` file

Create a new file named **`.env`** in the project folder:

```
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4.1-mini
TESSERACT_CMD=C:\Program Files\Tesseract-OCR	esseract.exe
```

---

# ▶️ Running the API

Start the server:

```bash
uvicorn main:app --reload
```

Visit Swagger UI:

```
http://127.0.0.1:8000/docs
```

---

# 📤 API Usage

### Endpoint

```
POST /extract-bill-data
```

### Request Example

```json
{
  "document": "https://your-public-url.com/sample_bill.pdf"
}
```

### Response Example

```json
{
  "is_success": true,
  "token_usage": {
    "total_tokens": 1234,
    "input_tokens": 900,
    "output_tokens": 334
  },
  "data": {
    "pagewise_line_items": [
      {
        "page_no": "1",
        "page_type": "Bill Detail",
        "bill_items": [
          {
            "item_name": "PARACETAMOL 650MG",
            "item_amount": 120.0,
            "item_rate": 12.0,
            "item_quantity": 10.0
          }
        ]
      }
    ],
    "total_item_count": 1
  }
}
```

---

# 🧠 How It Works

### 1. **Document Download**
Fetches the PDF/image from the supplied URL.

### 2. **OCR Pipeline**
- If PDF contains text → extracted directly  
- If scanned → converted to image and passed through Tesseract  
- Images (PNG/JPG) are OCR'd directly  

### 3. **LLM Extraction**
OCR text is sent to an LLM that extracts:
- item_name  
- item_quantity  
- item_rate  
- item_amount  
- page_type  

### 4. **Normalization**
Ensures clean numeric values and valid item entries.

### 5. **Final Output**
Returned in HackRx's exact required schema.

---

# 📊 Why This Approach Scores High

- Handles complex layouts & scanned bills  
- LLM fills missing fields (qty, rate) more accurately  
- Prevents double counting  
- Ignores subtotal / GST rows  
- Extracts items even when OCR breaks table formatting  
- Best possible accuracy under the allowed tools (LLMs permitted!)  

---

# ⚠️ Notes

- Input URL **must be publicly accessible**  
- Tesseract must be installed for scanned PDFs  
- LLM usage costs tokens — use GPT-4.1 mini or GPT-4o mini for cheaper runs  
- OCR quality highly affects extraction  

---

# 📬 Support

If you want:
- Dockerfile  
- Deployment  
- Prompt tuning  
- Cost-optimized hybrid approach  

Feel free to ask or open an issue.
