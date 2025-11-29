# parser_utils.py

import re
from typing import Dict, List


TOTAL_KEYWORDS = [
    "total",
    "sub total",
    "subtotal",
    "grand total",
    "net total",
    "round off",
    "roundoff",
]


def guess_page_type(lines: List[str]) -> str:
    """
    Very simple heuristic to classify page type.
    You can improve this later.
    """
    text = " ".join(lines).lower()

    if "pharmacy" in text or "medicine" in text or "tablet" in text:
        return "Pharmacy"
    if "final bill" in text or "bill summary" in text or "grand total" in text:
        return "Final Bill"

    return "Bill Detail"


def is_summary_line(line: str) -> bool:
    """
    Return True for lines that look like totals,
    which we do NOT want to treat as line items.
    """
    low = line.lower()
    return any(k in low for k in TOTAL_KEYWORDS)


def parse_line_to_item(line: str) -> Dict | None:
    """
    Try to parse a single line into a bill item.
    This is a very basic heuristic:
      - skip pure total/summary lines
      - require at least one digit + one letter
      - last number = amount
      - preceding numbers (if exist) = quantity & rate
    """
    line = line.strip()
    if not line:
        return None

    if is_summary_line(line):
        return None

    # must have at least one digit and one alphabetic character
    if not any(ch.isdigit() for ch in line) or not any(ch.isalpha() for ch in line):
        return None

    # extract all numbers on the line
    num_strings = re.findall(r"-?\d+(?:\.\d+)?", line)
    if not num_strings:
        return None

    try:
        numbers = [float(n) for n in num_strings]
    except ValueError:
        return None

    # amount assumed to be last number on the line
    amount = float(numbers[-1])
    rate = 0.0
    quantity = 0.0

    if len(numbers) >= 3:
        # ... qty, rate, amount
        rate = float(numbers[-2])
        quantity = float(numbers[-3])
    elif len(numbers) == 2:
        # ... qty, amount
        quantity = float(numbers[0])

    # item_name: everything before the first number
    first_num_match = re.search(r"-?\d+(?:\.\d+)?", line)
    if first_num_match:
        name = line[: first_num_match.start()].strip(" -:\t")
    else:
        name = line

    if not name:
        name = "ITEM"

    return {
        "item_name": name,
        "item_amount": amount,
        "item_rate": rate,
        "item_quantity": quantity,
    }


def extract_pagewise_line_items(pages_lines: List[List[str]]) -> List[Dict]:
    """
    Convert OCR'd text into the structure expected by the API.
    pages_lines: list of pages, each page is list of raw text lines.
    """
    result: List[Dict] = []

    for idx, lines in enumerate(pages_lines, start=1):
        bill_items: List[Dict] = []

        for line in lines:
            item = parse_line_to_item(line)
            if item:
                bill_items.append(item)

        page_dict = {
            "page_no": str(idx),
            "page_type": guess_page_type(lines),
            "bill_items": bill_items,
        }
        result.append(page_dict)

    return result
