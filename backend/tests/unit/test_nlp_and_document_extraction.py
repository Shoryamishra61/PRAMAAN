"""Tests for multilingual NLP engine and PDF/document extraction."""

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
from app.sandbox_api import NlpAnalyzeRequest, analyze_nlp_text, extract_document_payload


def test_detect_text_language() -> None:
    assert detect_text_language("Aapka refund kal process ho gaya tha")["language"] == "Hinglish (Romanized Hindi)"
    assert detect_text_language("कृपया मुझे मेरा रिफंड दें")["language"] == "Hindi (Devanagari)"
    assert detect_text_language("The refund of INR 4,999 was processed on 28 August.")["language"] == "English"


def test_extract_amounts_and_words() -> None:
    text = "Payment was INR 3,200 and later 500 rupaye was deducted."
    amounts = extract_amounts(text)
    norms = [a["normalized_inr"] for a in amounts]
    assert "3200.00" in norms
    assert "500.00" in norms

    word_text = "Merchant refunded do hazaar rupees."
    word_amounts = extract_amounts(word_text)
    assert any(a["normalized_inr"] == "2000.00" for a in word_amounts)


def test_extract_places_and_financial_entities() -> None:
    text = "Dispute escalated in Bengaluru and Mumbai via Razorpay and HDFC Bank."
    places = extract_places(text)
    assert "Bengaluru" in places
    assert "Mumbai" in places

    entities = extract_financial_entities(text)
    assert "Razorpay" in entities
    assert "HDFC Bank" in entities


def test_extract_transaction_references() -> None:
    text = "Payment ref pay_abc12345678 and bank UTR 123456789012 with dispute RF-HI-01."
    refs = extract_transaction_references(text)
    assert "pay_abc12345678" in refs
    assert "UTR: 123456789012" in refs
    assert "RF-HI-01" in refs


def test_classify_dispute_intent() -> None:
    assert classify_dispute_intent("Mera paisa wapas nahi aaya.")["intent"] == "REFUND_NOT_RECEIVED"
    assert classify_dispute_intent("Kat gaye do baar for same order.")["intent"] == "DOUBLE_DEBIT"
    assert classify_dispute_intent("Your refund was processed yesterday.")["intent"] == "REFUND_CLAIMED_PROCESSED"


def test_pdf_byte_stream_extraction() -> None:
    pdf_bytes = (
        b"%PDF-1.4\n1 0 obj\n<< /Length 120 >>\nstream\nBT\n/F1 12 Tf\n"
        b"(Your INR 3,200 refund was processed in Bengaluru, ref RF-HI-01.) Tj\nET\n"
        b"endstream\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    )
    extracted = extract_text_from_pdf_bytes(pdf_bytes)
    assert "INR 3,200 refund was processed" in extracted
    assert "Bengaluru" in extracted


def test_sandbox_nlp_and_document_payload() -> None:
    req = NlpAnalyzeRequest(text="Aapka INR 3,200 refund kal process ho gaya tha in Bengaluru.")
    res = analyze_nlp_text(req)
    assert res.language == "Hinglish (Romanized Hindi)"
    assert len(res.claimed_amounts) > 0
    assert res.claimed_amounts[0].normalized_inr == "3200.00"
    assert "Bengaluru" in res.places

    doc_res = extract_document_payload(
        "receipt.pdf",
        b"%PDF-1.4\nstream\nBT\n(INR 4,999 refund was processed.) Tj\nET\nendstream",
    )
    assert doc_res.file_type == "pdf"
    assert "INR 4,999 refund was processed." in doc_res.extracted_text
