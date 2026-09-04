from __future__ import annotations

import hmac

import pytest
from app.security import (
    WebhookSignatureError,
    compute_webhook_signature,
    verify_webhook_signature,
)

SECRET = b"synthetic-test-webhook-secret"
RAW_BODY = b'{"event":"payment.dispute.created","amount":250000}'


def test_exact_raw_body_with_valid_signature_passes() -> None:
    signature = compute_webhook_signature(RAW_BODY, SECRET)

    verify_webhook_signature(RAW_BODY, signature, SECRET)


@pytest.mark.parametrize("signature", [None, "", "not-hex", "00"])
def test_missing_or_malformed_signature_is_rejected(signature: str | None) -> None:
    with pytest.raises(WebhookSignatureError, match="validation failed") as captured:
        verify_webhook_signature(RAW_BODY, signature, SECRET)

    assert captured.value.code == "INGEST_SIGNATURE_INVALID"
    assert SECRET.decode() not in str(captured.value)


def test_body_mutation_after_signing_is_rejected() -> None:
    signature = compute_webhook_signature(RAW_BODY, SECRET)
    mutated = RAW_BODY.replace(b"250000", b"250001")

    with pytest.raises(WebhookSignatureError):
        verify_webhook_signature(mutated, signature, SECRET)


def test_whitespace_is_valid_when_it_is_part_of_exact_signed_bytes() -> None:
    transmitted = b'{\n  "event": "payment.dispute.created"\n}\n'
    signature = compute_webhook_signature(transmitted, SECRET)

    verify_webhook_signature(transmitted, signature, SECRET)
    with pytest.raises(WebhookSignatureError):
        verify_webhook_signature(transmitted.strip(), signature, SECRET)


def test_verifier_uses_constant_time_comparison(monkeypatch: pytest.MonkeyPatch) -> None:
    signature = compute_webhook_signature(RAW_BODY, SECRET)
    compared: list[tuple[str, str]] = []
    original_compare = hmac.compare_digest

    def recording_compare(left: str, right: str) -> bool:
        compared.append((left, right))
        return original_compare(left, right)

    monkeypatch.setattr(hmac, "compare_digest", recording_compare)

    verify_webhook_signature(RAW_BODY, signature, SECRET)

    assert compared == [(signature, signature)]
