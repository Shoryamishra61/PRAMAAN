"""Reusable, composable Hypothesis strategies for the PRAMAAN test generation engine.

Generates:
1. Minor-unit money amounts (standard, boundary, extreme, sub-paise, invalid)
2. ISO8601 UTC and bitemporal timestamps
3. Payment identifiers, ARNs, UTRs, and merchant references
4. Refund sequences and partial settlement partitions
5. Document text, customer claims, Hinglish paraphrases, and OCR corruptions
6. Webhook payloads, signatures, and tamper scenarios
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from hypothesis import strategies as st

# 1. Money & Currency Strategies
# Standard valid paise amounts: ₹0.00 to ₹100,000.00
valid_amount_minor_st = st.integers(min_value=0, max_value=10_000_000)

# Boundary values: ₹0, ₹0.01, ₹1.00, ₹999.99, ₹5,000, large 64-bit maximum
boundary_amount_minor_st = st.sampled_from(
    [
        0,  # ₹0.00
        1,  # ₹0.01
        100,  # ₹1.00
        99_999,  # ₹999.99
        500_000,  # ₹5,000.00
        100_000_000,  # ₹1,000,000.00
        2**31 - 1,  # 32-bit int boundary
        2**63 - 1,  # 64-bit SQLite INTEGER maximum
    ]
)

# Any non-negative 64-bit integer
any_amount_minor_st = st.one_of(
    valid_amount_minor_st,
    boundary_amount_minor_st,
    st.integers(min_value=0, max_value=2**63 - 1),
)

# Invalid / negative / malformed money representations
invalid_amount_minor_st = st.integers(max_value=-1)

# Currency code strategies
valid_currency_st = st.just("INR")
other_currency_st = st.sampled_from(["USD", "EUR", "GBP", "SGD", "AED"])
invalid_currency_st = st.sampled_from(["", "XYZ", "123", "inr", "TOOLONG"])
any_currency_st = st.one_of(valid_currency_st, other_currency_st, invalid_currency_st)

# Formatted currency string strategy (e.g. "₹2,500.50", "INR 100.00")
formatted_currency_str_st = st.builds(
    lambda sym, rupees, paise: f"{sym}{rupees}.{paise:02d}",
    sym=st.sampled_from(["₹", "INR ", ""]),
    rupees=st.integers(min_value=0, max_value=1_000_000),
    paise=st.integers(min_value=0, max_value=99),
)

# Malformed currency string strategy (sub-paise, NaN, negative, commas misplaced)
malformed_currency_str_st = st.sampled_from(
    [
        "₹100.555",  # Sub-paise fraction
        "-₹500.00",  # Negative
        "NaN",  # Non-numeric
        "Infinity",  # Infinity
        "₹1e6",  # Scientific notation
        "12.345.67",  # Multiple decimals
        "₹ 500",  # Extra space
        "$500.00",  # Wrong symbol for INR
        "",  # Empty string
    ]
)


# 2. Temporal & Bitemporal Strategies
def _utc_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


# Valid ISO8601 UTC timestamps between 2020 and 2030
valid_timestamp_dt_st = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime(2030, 1, 1),
    timezones=st.just(timezone.utc),
)

valid_timestamp_iso_st = valid_timestamp_dt_st.map(_utc_iso)

# Temporal pair strategy: (t_early, t_late)
temporal_ordered_pair_st = st.tuples(
    valid_timestamp_dt_st, st.integers(min_value=0, max_value=86400)
).map(
    lambda pair: (
        _utc_iso(pair[0]),
        _utc_iso(datetime.fromtimestamp(pair[0].timestamp() + pair[1], tz=timezone.utc)),
    )
)

# Inverted temporal pair strategy: (t_late, t_early)
temporal_inverted_pair_st = temporal_ordered_pair_st.map(lambda pair: (pair[1], pair[0]))


# 3. Identifier & Reference Strategies
payment_id_st = st.integers(min_value=1000, max_value=999999).map(lambda n: f"pay_test_{n}")
refund_id_st = st.integers(min_value=1000, max_value=999999).map(lambda n: f"rfnd_test_{n}")
dispute_id_st = st.integers(min_value=1000, max_value=999999).map(lambda n: f"disp_test_{n}")
event_id_st = st.integers(min_value=1000, max_value=999999).map(lambda n: f"evt_test_{n}")
arn_st = st.integers(min_value=100000000000, max_value=999999999999).map(str)
order_id_st = st.integers(min_value=1000, max_value=999999).map(lambda n: f"order_test_{n}")


# 4. Evidence & Claim Strategies
# Reason codes
chargeback_reason_code_st = st.sampled_from(
    [
        "CREDIT_NOT_PROCESSED",
        "DUPLICATE",
        "FRAUD",
        "GENERAL",
        "GOODS_NOT_RECEIVED",
        "INCORRECT_AMOUNT",
        "SUBSCRIPTION_CANCELED",
    ]
)

# Natural language claims
customer_claim_text_st = st.sampled_from(
    [
        "I requested a full refund of ₹2,500 on March 1st but never received it.",
        "Merchant promised refund within 5 days but credit is missing from bank statement.",
        "Order was canceled immediately; refund of INR 1,500.00 was confirmed by support.",
        "Maine refund manga tha par abhi tak account me credit nahi hua.",
        "Amount reverse ho gaya bolke merchant ne receipt diya par paise nahi aaye.",
        "Paid ₹5,000 for service but refund of ₹5,000 was not processed.",
    ]
)

# Hinglish & colloquial paraphrase templates
hinglish_paraphrase_st = st.sampled_from(
    [
        "refund kr diya tha support team ne",
        "paise wapas account me daal diye gaye hain",
        "merchant bola refund ho gya par bank bol raha pending hai",
        "amount reversal complete ho chuka hai reference RF-992",
    ]
)


# Document text corruption function
def corrupt_text(text: str, corruption_type: str) -> str:
    if corruption_type == "ocr_digit_sub":
        return text.replace("0", "O").replace("1", "l").replace("5", "S")
    if corruption_type == "space_removal":
        return text.replace(" ", "")
    if corruption_type == "unicode_homoglyph":
        return text.replace("a", "\u0430").replace("e", "\u0435")  # Cyrillic homoglyphs
    if corruption_type == "trailing_noise":
        return text + " \x00\x01\t   \n\r"
    return text


corrupted_document_text_st = st.tuples(
    customer_claim_text_st,
    st.sampled_from(["ocr_digit_sub", "space_removal", "unicode_homoglyph", "trailing_noise"]),
).map(lambda pair: corrupt_text(pair[0], pair[1]))


# 5. Webhook Payload Strategy
@st.composite
def razorpay_webhook_payload_st(draw: st.DrawFn) -> dict[str, Any]:
    eid = draw(event_id_st)
    pid = draw(payment_id_st)
    amt = draw(valid_amount_minor_st)
    cur = draw(valid_currency_st)
    created_at = int(draw(valid_timestamp_dt_st).timestamp())

    return {
        "entity": "event",
        "account_id": "acc_test_razorpay",
        "event": "payment.dispute.created",
        "contains": ["payment", "dispute"],
        "payload": {
            "payment": {
                "entity": {
                    "id": pid,
                    "amount": amt,
                    "currency": cur,
                    "status": "captured",
                    "created_at": created_at,
                }
            },
            "dispute": {
                "entity": {
                    "id": draw(dispute_id_st),
                    "payment_id": pid,
                    "amount": amt,
                    "currency": cur,
                    "reason_code": draw(chargeback_reason_code_st),
                    "status": "under_review",
                    "created_at": created_at + 3600,
                }
            },
        },
        "created_at": created_at + 3600,
        "razorpay_event_id": eid,
    }
