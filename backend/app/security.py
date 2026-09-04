"""Security primitives for inbound Razorpay-compatible webhook authentication."""

from __future__ import annotations

import hashlib
import hmac


class WebhookSignatureError(ValueError):
    """Reject an unauthenticated webhook without exposing verification material."""

    code = "INGEST_SIGNATURE_INVALID"


def compute_webhook_signature(raw_body: bytes, secret: bytes) -> str:
    """Compute HMAC-SHA256 over the exact transmitted request bytes."""
    return hmac.new(secret, raw_body, hashlib.sha256).hexdigest()


def verify_webhook_signature(
    raw_body: bytes, supplied_signature: str | None, secret: bytes
) -> None:
    """Raise when signature material is absent, malformed, or mismatched."""
    if not supplied_signature or not secret:
        raise WebhookSignatureError("Webhook signature validation failed.")

    normalized_signature = supplied_signature.strip().lower()
    if len(normalized_signature) != hashlib.sha256().digest_size * 2:
        raise WebhookSignatureError("Webhook signature validation failed.")
    try:
        bytes.fromhex(normalized_signature)
    except ValueError as error:
        raise WebhookSignatureError("Webhook signature validation failed.") from error

    expected_signature = compute_webhook_signature(raw_body, secret)
    if not hmac.compare_digest(expected_signature, normalized_signature):
        raise WebhookSignatureError("Webhook signature validation failed.")
