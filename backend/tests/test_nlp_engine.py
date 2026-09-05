"""Comprehensive test suite for Multilingual NLP Engine and Document Extraction.

Tests:
1. Script & Language Detection (Hindi Devanagari, Hinglish, Bengali, Tamil, Telugu, Kannada, Marathi, English)
2. Verbal Numeral and Currency Normalization ("do hazaar", "paanch sau", "10k", "lakh", "rupaye", "₹")
3. Indian Commercial Hubs and Place Entity Recognition (100+ cities)
4. Payment Rails, Banks, UPI VPAs, UTR/RRN numbers, and Razorpay IDs
5. Dispute Intent Categorization across distinct consumer dispute patterns
6. Edge Cases, Adversarial Strings, Mixed Scripts, and Empty Inputs
7. Fast Sandbox API Endpoints (/api/v1/sandbox/nlp-analyze and /api/v1/sandbox/extract-document)
"""

from __future__ import annotations

import base64
from pathlib import Path
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.nlp_engine import (
    analyze_multilingual_dispute,
    classify_dispute_intent,
    detect_text_language,
    extract_amounts,
    extract_financial_entities,
    extract_places,
    extract_text_from_pdf_bytes,
    extract_transaction_references,
)


def test_multilingual_script_and_language_detection() -> None:
    # 1. Hindi in Devanagari
    res_hi = detect_text_language("कृपया मेरा 500 रुपये का रिफंड वापस करो")
    assert res_hi["language"] == "Hindi (Devanagari)"
    assert res_hi["confidence"] >= 0.90

    # 2. Hinglish (Romanized Hindi)
    res_hing = detect_text_language("Mera refund nahi mila abhi tak, paise wapas karo kal tak.")
    assert res_hing["language"] == "Hinglish (Romanized Hindi)"
    assert res_hing["confidence"] >= 0.70

    # 3. Bengali Script
    res_bn = detect_text_language("আমার টাকা এখনও পাইনি দয়া করে ফেরত দিন")
    assert res_bn["language"] == "Bengali"

    # 4. Tamil Script
    res_ta = detect_text_language("பணம் இன்னும் வரவில்லை தயவுசெய்து பணத்தைத் திருப்பித் தரவும்")
    assert res_ta["language"] == "Tamil"

    # 5. Telugu Script
    res_te = detect_text_language("నా డబ్బులు ఇంకా రాలేదు రీఫండ్ చేయండి")
    assert res_te["language"] == "Telugu"

    # 6. Kannada Script
    res_kn = detect_text_language("ನನ್ನ ಹಣ ಇನ್ನೂ ಬಂದಿಲ್ಲ ದಯವಿಟ್ಟು ಮರುಪಾವತಿ ಮಾಡಿ")
    assert res_kn["language"] == "Kannada"

    # 7. Romanized Regional markers
    assert detect_text_language("Taka ferot paini")["language"] == "Bengali"
    assert detect_text_language("Panam kidaikkavillai")["language"] == "Tamil"
    assert detect_text_language("Dabbulu raledu ayindi")["language"] == "Telugu"
    assert detect_text_language("Paise parat aale nahit")["language"] == "Marathi"

    # 8. English
    res_en = detect_text_language("Customer has requested a full refund of 2500 INR for order.")
    assert res_en["language"] == "English"


def test_amount_and_verbal_numeral_extraction() -> None:
    # Numeric with currency symbol
    amounts = extract_amounts("Debited ₹ 3,200.50 from account.")
    assert any(a["normalized_inr"] == "3200.50" and a["minor_units"] == 320050 for a in amounts)

    # Word numerals in Hinglish: "do hazaar" -> 2000
    amounts_words = extract_amounts("Claimed do hazaar rupaye was not received.")
    assert any(a["normalized_inr"] == "2000.00" and a["minor_units"] == 200000 for a in amounts_words)

    # Combined: "paanch sau" -> 500
    amounts_sau = extract_amounts("Customer paid paanch sau rupees.")
    assert any(a["normalized_inr"] == "500.00" and a["minor_units"] == 50000 for a in amounts_sau)

    # Multiplier: "10k" -> 10000
    amounts_k = extract_amounts("Total amount of 10k rs.")
    assert any(a["normalized_inr"] == "10000.00" and a["minor_units"] == 1000000 for a in amounts_k)

    # Lakh: "teen lakh" -> 300000
    amounts_lakh = extract_amounts("Merchant paid teen lakh rupees.")
    assert any(a["normalized_inr"] == "300000.00" and a["minor_units"] == 30000000 for a in amounts_lakh)


def test_indian_places_extraction() -> None:
    text = "Order shipped from Bengaluru warehouse, routed through Mumbai and delivered in Jaipur."
    places = extract_places(text)
    assert "Bengaluru" in places
    assert "Mumbai" in places
    assert "Jaipur" in places

    # Case insensitive matching
    text_lower = "Customer located in hyderabad near charminar and chennai office."
    places_lower = extract_places(text_lower)
    assert "Hyderabad" in places_lower
    assert "Chennai" in places_lower


def test_financial_entities_and_rails() -> None:
    text = (
        "Transaction made via Razorpay on HDFC Bank UPI handle user@oksbi, "
        "bank reference UTR 492019284719, gateway id pay_H982abCdef1234, dispute RF-HI-01."
    )
    entities = extract_financial_entities(text)
    assert "Razorpay" in entities
    assert "HDFC Bank" in entities
    assert "UPI" in entities

    refs = extract_transaction_references(text)
    assert "user@oksbi" in refs
    assert "UTR: 492019284719" in refs
    assert "pay_H982abCdef1234" in refs
    assert "RF-HI-01" in refs


def test_dispute_intent_classification() -> None:
    # 1. Refund not received
    intent_not_received = classify_dispute_intent("Mera refund nahi mila abhi tak.")
    assert intent_not_received["intent"] == "REFUND_NOT_RECEIVED"

    # 2. Double debit
    intent_double = classify_dispute_intent("Amount was debited two times / do baar cut gaya.")
    assert intent_double["intent"] == "DOUBLE_DEBIT"

    # 3. Claimed processed
    intent_claimed = classify_dispute_intent("Merchant confirmed refund has been processed.")
    assert intent_claimed["intent"] == "REFUND_CLAIMED_PROCESSED"

    # 4. Return delivered but no refund
    intent_return = classify_dispute_intent("Returned the product and parcel delivered but no refund.")
    assert intent_return["intent"] == "RETURN_DELIVERED_NO_REFUND"

    # 5. Unauthorized transaction
    intent_fraud = classify_dispute_intent("Fraudulent charge, unapproved transaction, not authorized.")
    assert intent_fraud["intent"] == "UNAUTHORIZED_TRANSACTION"


def test_comprehensive_multilingual_packet() -> None:
    text = (
        "Aapka INR 3,200 refund kal process ho gaya tha in Bengaluru via Razorpay "
        "to user@okhdfcbank, reference RF-HI-01."
    )
    packet = analyze_multilingual_dispute(text)
    assert packet["language"] == "Hinglish (Romanized Hindi)"
    assert packet["confidence"] >= 0.70
    assert any(a["normalized_inr"] == "3200.00" for a in packet["claimed_amounts"])
    assert "Bengaluru" in packet["places"]
    assert "Razorpay" in packet["banks_and_rails"]
    assert "user@okhdfcbank" in packet["transaction_references"]
    assert "RF-HI-01" in packet["transaction_references"]


def test_adversarial_and_empty_inputs_do_not_crash() -> None:
    # Empty string
    empty_res = analyze_multilingual_dispute("")
    assert empty_res["language"] == "English"
    assert empty_res["claimed_amounts"] == []

    # Huge string of unspecific repetition falls back safely to GENERAL_INQUIRY
    huge_res = analyze_multilingual_dispute("refund " * 1000)
    assert huge_res["intent"] == "GENERAL_INQUIRY"

    # Specific repeated complaint resolves intent accurately
    specific_res = analyze_multilingual_dispute("I need refund for this order. " * 50)
    assert specific_res["intent"] == "REFUND_NOT_RECEIVED"

    # Mixed scripts and emoji
    emoji_res = analyze_multilingual_dispute("💸 ₹500 का रिफंड wapas karo in Mumbai @oksbi 🎉")
    assert emoji_res["language"] in ("Hindi (Devanagari)", "Hinglish (Romanized Hindi)")
    assert any(a["normalized_inr"] == "500.00" for a in emoji_res["claimed_amounts"])
    assert "Mumbai" in emoji_res["places"]


def test_sandbox_nlp_and_document_endpoints(tmp_path: Path) -> None:
    client = TestClient(create_app(Settings(database_path=tmp_path / "sandbox.sqlite3")))

    # 1. Test POST /api/v1/sandbox/nlp-analyze
    nlp_req = {
        "text": "Mera INR 2,500 refund nahi mila in Delhi via Google Pay ref 847291029384"
    }
    nlp_resp = client.post("/api/v1/sandbox/nlp-analyze", json=nlp_req)
    assert nlp_resp.status_code == 200
    data = nlp_resp.json()
    assert data["language"] == "Hinglish (Romanized Hindi)"
    assert any(a["normalized_inr"] == "2500.00" for a in data["claimed_amounts"])
    assert "Delhi" in data["places"]
    assert "Google Pay" in data["banks_and_rails"]
    assert "UTR: 847291029384" in data["transaction_references"]

    # 2. Test POST /api/v1/sandbox/extract-document (Text file)
    txt_doc = {
        "filename": "dispute_claim.txt",
        "content_text": "Customer complaint from Pune regarding 1500 rupaye debit.",
    }
    txt_resp = client.post("/api/v1/sandbox/extract-document", json=txt_doc)
    assert txt_resp.status_code == 200
    txt_data = txt_resp.json()
    assert txt_data["file_type"] == "text"
    assert "Pune" in txt_data["nlp"]["places"]
    assert any(a["normalized_inr"] == "1500.00" for a in txt_data["nlp"]["claimed_amounts"])

    # 3. Test POST /api/v1/sandbox/extract-document (Base64 simulated PDF)
    raw_pdf = b"%PDF-1.4\n1 0 obj\n<< /Length 50 >>\nstream\nBT /F1 12 Tf (Refund of INR 4500 processed in Jaipur) Tj ET\nendstream\nendobj\n%%EOF"
    pdf_doc = {
        "filename": "settlement_notice.pdf",
        "content_base64": base64.b64encode(raw_pdf).decode("ascii"),
    }
    pdf_resp = client.post("/api/v1/sandbox/extract-document", json=pdf_doc)
    assert pdf_resp.status_code == 200
    pdf_data = pdf_resp.json()
    assert pdf_data["file_type"] == "pdf"
    assert "INR 4500" in pdf_data["extracted_text"]
    assert "Jaipur" in pdf_data["nlp"]["places"]
