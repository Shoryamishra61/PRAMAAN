from __future__ import annotations

from app.profile import (
    DEFAULT_PROFILE_ID,
    load_default_profile,
    missing_suggested_evidence,
    resolve_profile,
)


def test_canonical_profile_loads_with_suggested_evidence_semantics() -> None:
    profile = load_default_profile()

    assert profile.profile_id == DEFAULT_PROFILE_ID
    assert profile.review_if_missing is True
    assert profile.suggested_evidence == (
        "refund_generation_or_ledger_state",
        "customer_refund_communication",
        "refund_policy_if_relevant",
        "transaction_reversal_or_credit_state_if_available",
    )
    assert (
        "Suggested evidence is not treated as universally mandatory network evidence."
        in profile.notes
    )


def test_missing_suggested_evidence_is_exposed_for_review() -> None:
    profile = load_default_profile()

    missing = missing_suggested_evidence(
        profile,
        {"refund_generation_or_ledger_state", "customer_refund_communication"},
    )

    assert missing == (
        "refund_policy_if_relevant",
        "transaction_reversal_or_credit_state_if_available",
    )
    assert profile.review_if_missing is True


def test_unsupported_local_profile_resolves_out_of_scope() -> None:
    resolution = resolve_profile("another_reason_family")

    assert resolution.supported is False
    assert resolution.profile is None
    assert resolution.review_reason == "OUT_OF_SCOPE"


def test_raw_reason_code_is_not_used_as_local_profile() -> None:
    resolution = resolve_profile("RZP04")

    assert resolution.supported is False
    assert resolution.review_reason == "OUT_OF_SCOPE"
