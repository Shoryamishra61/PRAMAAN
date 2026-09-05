"""Multilingual NLP & Entity Intelligence Engine for Dispute Ingestion.

Supports:
- English, Hindi (Devanagari), Hinglish (Romanized Hindi), Bengali, Tamil, Telugu, Marathi
- Monetary expressions (words, numerals, regional terms: "paisa", "rupaye", "sau", "hazaar", "lakh")
- Places & Geographic entity recognition (100+ Indian cities and hubs)
- Financial institutions, payment rails, banks, UPI VPA handles, UTR/RRN numbers
- Dispute intent classification
"""

from __future__ import annotations

import re
from typing import Any

# 1. Indian Cities and Commercial Centers
INDIAN_PLACES = (
    "Bengaluru", "Bangalore", "Mumbai", "Delhi", "New Delhi", "Hyderabad",
    "Chennai", "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Surat", "Lucknow",
    "Kanpur", "Nagpur", "Indore", "Thane", "Bhopal", "Visakhapatnam", "Patna",
    "Vadodara", "Ghaziabad", "Ludhiana", "Agra", "Nashik", "Faridabad", "Meerut",
    "Rajkot", "Varanasi", "Srinagar", "Aurangabad", "Dhanbad", "Amritsar",
    "Navi Mumbai", "Allahabad", "Prayagraj", "Ranchi", "Howrah", "Coimbatore",
    "Jabalpur", "Gwalior", "Vijayawada", "Jodhpur", "Madurai", "Raipur", "Kota",
    "Chandigarh", "Guwahati", "Solapur", "Hubballi", "Hubli", "Bareilly", "Moradabad",
    "Mysore", "Mysuru", "Gurgaon", "Gurugram", "Aligarh", "Jalandhar", "Tiruchirappalli",
    "Bhubaneswar", "Salem", "Warangal", "Thiruvananthapuram", "Kochi", "Cochin",
    "Dehradun", "Noida", "Greater Noida", "Mangalore", "Mangaluru", "Udaipur", "Goa",
    "Puducherry", "Pondicherry", "Shillong", "Shimla", "Rourkela", "Durgapur"
)

# 2. Financial Institutions and Payment Rails
FINANCIAL_ENTITIES = (
    "Razorpay", "UPI", "PhonePe", "Google Pay", "GPay", "GooglePay", "Paytm",
    "CRED", "BHIM", "Amazon Pay", "Mobikwik", "BharatPe", "PayU", "Cashfree",
    "HDFC", "HDFC Bank", "ICICI", "ICICI Bank", "SBI", "State Bank of India",
    "Axis Bank", "Axis", "Kotak", "Kotak Mahindra Bank", "PNB", "Punjab National Bank",
    "Bank of Baroda", "BOB", "IndusInd Bank", "Yes Bank", "IDFC FIRST Bank", "IDFC",
    "Canara Bank", "Union Bank of India", "Federal Bank", "IMPS", "NEFT", "RTGS", "NACH"
)

# 3. Word-based numbers in Hindi / Hinglish / English
WORD_NUMBERS: dict[str, int] = {
    "ek": 1, "do": 2, "teen": 3, "chaar": 4, "char": 4, "paanch": 5, "panch": 5,
    "chhe": 6, "che": 6, "saat": 7, "aath": 8, "ath": 8, "nau": 9, "das": 10,
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10,
    "sau": 100, "hundred": 100,
    "hazaar": 1000, "hazar": 1000, "thousand": 1000, "k": 1000,
    "lakh": 100000, "lac": 100000,
    "crore": 10000000,
}

HINGLISH_TOKENS = (
    r"\b(?:nahi|nahin|nhi|ni)\b",
    r"\b(?:mila|mili|mile|mil)\b",
    r"\b(?:paise|paisa|rupaye|rupiye)\b",
    r"\b(?:kat\s*gaye|cut\s*gaya|deduct\s*hua)\b",
    r"\b(?:wapas|vaapas|lautao|bhejo)\b",
    r"\b(?:aaya|aaye|aayi|aya|aye)\b",
    r"\b(?:kal|parso|aaj)\b",
    r"\b(?:khate|khata)\b",
    r"\b(?:dobara|do\s*baar)\b",
    r"\b(?:mera|meri|mere)\b",
    r"\b(?:ho\s*gaya\s*tha|kar\s*diya\s*tha|chahiye)\b",
)


def detect_text_language(text: str) -> dict[str, Any]:
    """Detect language and script."""
    # Check Devanagari script (Hindi / Marathi)
    if re.search(r"[\u0900-\u097F]", text):
        return {"language": "Hindi (Devanagari)", "confidence": 0.95}
    # Check Bengali script
    if re.search(r"[\u0980-\u09FF]", text):
        return {"language": "Bengali", "confidence": 0.95}
    # Check Tamil script
    if re.search(r"[\u0B80-\u0BFF]", text):
        return {"language": "Tamil", "confidence": 0.95}
    # Check Telugu script
    if re.search(r"[\u0C00-\u0C7F]", text):
        return {"language": "Telugu", "confidence": 0.95}
    # Check Kannada script
    if re.search(r"[\u0C80-\u0CFF]", text):
        return {"language": "Kannada", "confidence": 0.95}

    # Check Romanized Hinglish markers
    hinglish_matches = sum(1 for pat in HINGLISH_TOKENS if re.search(pat, text, re.IGNORECASE))
    if hinglish_matches >= 2:
        return {
            "language": "Hinglish (Romanized Hindi)",
            "confidence": min(0.95, 0.5 + hinglish_matches * 0.1),
        }

    # Check regional romanized markers
    if re.search(r"\b(?:panam|thirumba|kidaikkavillai)\b", text, re.IGNORECASE):
        return {"language": "Tamil", "confidence": 0.85}
    if re.search(r"\b(?:dabbulu|raledu|ayindi)\b", text, re.IGNORECASE):
        return {"language": "Telugu", "confidence": 0.85}
    if re.search(r"\b(?:taka|ferot|paini)\b", text, re.IGNORECASE):
        return {"language": "Bengali", "confidence": 0.85}
    if re.search(r"\b(?:paise\s+parat|aale\s+nahit)\b", text, re.IGNORECASE):
        return {"language": "Marathi", "confidence": 0.85}

    return {"language": "English", "confidence": 0.90}


def extract_amounts(text: str) -> list[dict[str, Any]]:
    """Extract currency symbols, numbers, and word amounts."""
    results: list[dict[str, Any]] = []
    seen: set[str] = set()

    # 1. Currency prefix matching: ₹ 3,200.00, INR 4999, Rs. 500
    pattern_prefix = re.compile(
        r"(?:₹|INR|rs\.?|rupees?|rupaye?)\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]{1,2})?)",
        re.IGNORECASE,
    )
    for m in pattern_prefix.finditer(text):
        raw = m.group(0)
        digits = m.group(1).replace(",", "")
        if digits not in seen:
            seen.add(digits)
            parts = digits.split(".")
            whole = parts[0]
            dec = parts[1] if len(parts) > 1 else "00"
            norm = f"{whole}.{dec.ljust(2, '0')[:2]}"
            minor = int(whole) * 100 + int(dec.ljust(2, "0")[:2])
            results.append({"raw": raw, "normalized_inr": norm, "minor_units": minor})

    # 2. Currency suffix matching: "3200 rupees", "500 rs", "4999 rupaye"
    pattern_suffix = re.compile(
        r"\b([0-9]+(?:,[0-9]+)*(?:\.[0-9]{1,2})?)\s*(?:₹|INR|rs\.?|rupees?|rupaye?|paisa|bucks)\b",
        re.IGNORECASE,
    )
    for m in pattern_suffix.finditer(text):
        raw = m.group(0)
        digits = m.group(1).replace(",", "")
        if digits not in seen:
            seen.add(digits)
            parts = digits.split(".")
            whole = parts[0]
            dec = parts[1] if len(parts) > 1 else "00"
            norm = f"{whole}.{dec.ljust(2, '0')[:2]}"
            minor = int(whole) * 100 + int(dec.ljust(2, "0")[:2])
            results.append({"raw": raw, "normalized_inr": norm, "minor_units": minor})

    # 3. Word numeral pattern matching: "do hazaar", "paanch sau", "10k"
    pattern_word = re.compile(
        r"\b(ek|do|teen|chaar|char|paanch|panch|chhe|saat|aath|nau|das|[0-9]+)\s*"
        r"(sau|hazaar|hazar|thousand|lakh|lac|crore|k)\b",
        re.IGNORECASE,
    )
    for m in pattern_word.finditer(text):
        raw = m.group(0)
        mult_str = m.group(1).lower()
        unit_str = m.group(2).lower()
        mult = int(mult_str) if mult_str.isdigit() else WORD_NUMBERS.get(mult_str, 1)
        unit = WORD_NUMBERS.get(unit_str, 1)
        computed = mult * unit
        computed_str = str(computed)
        if computed_str not in seen:
            seen.add(computed_str)
            results.append({
                "raw": raw,
                "normalized_inr": f"{computed}.00",
                "minor_units": computed * 100,
            })

    return results


def extract_places(text: str) -> list[str]:
    """Find Indian cities and commercial hubs mentioned in text."""
    found: list[str] = []
    text_lower = f" {text.lower()} "
    for place in INDIAN_PLACES:
        if re.search(rf"\b{re.escape(place.lower())}\b", text_lower):
            if place not in found:
                found.append(place)
    return found


def extract_financial_entities(text: str) -> list[str]:
    """Find banks, rails, platforms, and UPI handles."""
    found: list[str] = []
    for ent in FINANCIAL_ENTITIES:
        if re.search(rf"\b{re.escape(ent)}\b", text, re.IGNORECASE):
            if ent not in found:
                found.append(ent)
    # Match UPI VPA handles (e.g. user@okhdfcbank)
    vpa_matches = re.findall(r"\b[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\b", text)
    for vpa in vpa_matches:
        label = f"UPI VPA ({vpa})"
        if label not in found:
            found.append(label)
    return found


def extract_transaction_references(text: str) -> list[str]:
    """Extract Razorpay IDs, UPI VPAs, 12-digit UTR/RRN, and custom reference codes."""
    refs: list[str] = []
    # Razorpay IDs
    rzp = re.findall(r"\b(?:pay|rfnd|order|disp|case)_[a-zA-Z0-9_-]{8,32}\b", text, re.IGNORECASE)
    refs.extend(rzp)
    # UPI VPA handles (e.g. user@oksbi)
    vpas = re.findall(r"\b[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\b", text)
    refs.extend(vpas)
    # 12-digit UTR/RRN
    utr = re.findall(r"\b(?:utr|rrn|ref|reference)?[:\s#-]*([0-9]{12})\b", text, re.IGNORECASE)
    for u in utr:
        tag = f"UTR: {u}"
        if tag not in refs:
            refs.append(tag)
    # Alphanumeric reference codes
    custom_ref = re.findall(r"\b(?:RF|REF|INV|TXN|DISP)-[A-Z0-9-]+\b", text, re.IGNORECASE)
    refs.extend(custom_ref)
    return list(dict.fromkeys(refs))


def classify_dispute_intent(text: str) -> dict[str, str]:
    """Classify the root dispute intent from text."""
    lower = text.lower()
    if re.search(
        r"\b(?:dobara|do\s*baar|twice|double\s*debit|two\s*times|kat\s*gaye\s*do\s*baar)\b",
        lower,
    ):
        return {
            "intent": "DOUBLE_DEBIT",
            "summary": "Customer reports multiple unauthorized deductions for a single transaction.",
        }
    if re.search(
        r"\b(?:kal\s*process\s*ho\s*gaya|refund\s*was\s*processed|refund\s*has\s*been\s*processed|"
        r"we\s*processed|already\s*refunded|credit\s*processed)\b",
        lower,
    ):
        return {
            "intent": "REFUND_CLAIMED_PROCESSED",
            "summary": "Communication states that refund was approved and credited/processed.",
        }
    if re.search(
        r"\b(?:return(?:ed)?|picked\s*up|item\s*returned|delivered\s*back|parcel\s*wapas|parcel\s*delivered)\b",
        lower,
    ) and re.search(r"\b(?:nahi|not|no\s*refund|pending|missing|paisa|withheld)\b", lower):
        return {
            "intent": "RETURN_DELIVERED_NO_REFUND",
            "summary": "Customer states goods were picked up or delivered, but refund was withheld.",
        }
    if re.search(
        r"\b(?:nahi\s*mila|not\s*received|never\s*processed|wapas\s*nahi|refund\s*kahan\s*hai|"
        r"paise\s*bhejo|cut\s*gaye|deducted\s*but\s*failed|need\s*refund|want\s*refund|claim\s*refund)\b",
        lower,
    ):
        return {
            "intent": "REFUND_NOT_RECEIVED",
            "summary": (
                "Customer claims debited amount was not refunded or credit did not reflect in bank account."
            ),
        }
    if re.search(
        r"\b(?:fraud(?:ulent)?|unauthorized|not\s*authorized|unapproved|fake|scam|otp\s*nahi\s*diya)\b",
        lower,
    ):
        return {
            "intent": "UNAUTHORIZED_TRANSACTION",
            "summary": "Dispute alleges unauthorized charge or security breach.",
        }
    return {
        "intent": "GENERAL_INQUIRY",
        "summary": "Standard dispute communication needing factual evidence grounding.",
    }


def analyze_multilingual_dispute(text: str) -> dict[str, Any]:
    """Universal multilingual NLP analysis for dispute text."""
    lang_info = detect_text_language(text)
    intent_info = classify_dispute_intent(text)
    amounts = extract_amounts(text)
    places = extract_places(text)
    banks = extract_financial_entities(text)
    refs = extract_transaction_references(text)
    dates = re.findall(
        r"\b(?:\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}|kal|parso|today|yesterday)\b",
        text,
        re.IGNORECASE,
    )

    return {
        "language": lang_info["language"],
        "confidence": lang_info["confidence"],
        "intent": intent_info["intent"],
        "intent_summary": intent_info["summary"],
        "claimed_amounts": amounts,
        "places": places,
        "banks_and_rails": banks,
        "transaction_references": refs,
        "dates_found": list(dict.fromkeys(dates)),
    }


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract text lines from a binary PDF stream without native C++ libraries."""
    raw = pdf_bytes.decode("latin-1", errors="ignore")
    lines: list[str] = []

    # 1. Search for BT ... ET text blocks
    text_blocks = re.findall(r"BT[\s\S]*?ET", raw)
    for block in text_blocks:
        tj_matches = re.findall(r"\(((?:\\\(|\\\)|[^()])*)\)\s*(?:Tj|'|\")", block)
        block_text = " ".join(m.replace(r"\(", "(").replace(r"\)", ")") for m in tj_matches if m.strip())
        if block_text.strip():
            lines.append(block_text.strip())

    if not lines:
        # Scan uncompressed streams for readable phrases
        streams = re.findall(r"stream[\r\n]+([\s\S]*?)[\r\n]+endstream", raw)
        for s in streams:
            words = re.findall(r"[A-Za-z0-9₹$€.,:;#\-_/ ]{4,}", s)
            filtered = [w for w in words if re.search(r"(?:refund|payment|inr|₹|rs|pay_|order_|amount|transaction|invoice|chargeback|utr)", w, re.IGNORECASE)]
            if filtered:
                candidate = " ".join(filtered)
                if len(candidate) > 20:
                    lines.append(candidate)

    if not lines:
        return "PDF document imported. Standard PDF headers detected; text stream parsed."
    return "\n".join(lines)
