"""CARVE typed contracts and deterministic proof compiler.

Learned scores are accepted only by a later selective controller. This module owns hard invariant
precedence and never calls a payment or dispute write API.
"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Literal

import z3
from pydantic import BaseModel, ConfigDict, Field


class DecisionStatus(str, Enum):
    PASS = "PASS"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class SourceAuthorityTier(str, Enum):
    TIER_0 = "TIER_0"  # authoritative processor/merchant ledger
    TIER_1 = "TIER_1"  # carrier / payment-network / signed system record
    TIER_2 = "TIER_2"  # merchant operational document
    TIER_3 = "TIER_3"  # customer communication
    TIER_4 = "TIER_4"  # free-form analyst note
    TIER_5 = "TIER_5"  # model-derived interpretation


class CircuitBreakerState(str, Enum):
    AUTOMATION_ENABLED = "AUTOMATION_ENABLED"
    DEGRADED = "DEGRADED"
    REVIEW_ONLY = "REVIEW_ONLY"


class EvidenceArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    case_id: str
    source_type: str
    source_system: str
    source_uri: str
    ingested_at: str
    parser_version: str
    content: str
    structured_payload: dict[str, Any]
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    acquisition_cost: int = Field(ge=0)
    event_time: str | None = None
    available_time: str | None = None
    source_authority: SourceAuthorityTier = SourceAuthorityTier.TIER_0


class GroundedClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str
    relation: str
    source_document: str
    source_quote: str
    source_span: tuple[int, int]
    attributes: dict[str, Any]
    grounded: bool


class TypedRelation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relation_id: str
    type: str
    subject: str
    object: str
    source_document: str
    source_span: tuple[int, int]


class ProofFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fact_id: str
    kind: Literal["GROUNDED_CLAIM", "AUTHORITATIVE_FACT", "INVARIANT"]
    field: str
    value: Any
    evidence_id: str | None = None
    source_span: tuple[int, int] | None = None


class ContradictionCertificate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    certificate_id: str
    case_id: str
    solver: Literal["Z3"] = "Z3"
    solver_status: Literal["UNSAT"] = "UNSAT"
    invariant_id: str
    facts: tuple[ProofFact, ...]
    evidence_ids: tuple[str, ...]
    minimal_relative_to_compiled_constraints: bool
    proof_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class InvariantResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    status: Literal["SAT", "UNSAT", "INCOMPLETE", "ERROR"]
    invariant_id: str | None
    missing_evidence: tuple[str, ...] = ()
    certificate: ContradictionCertificate | None = None
    reason: str
    hard_authority: bool = True
    model_override_allowed: bool = False


class RiskPrediction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_id: str
    residual_risk: float = Field(ge=0, le=1)
    artifact_sha256: str


class RiskCertificate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    calibration_id: str
    pass_threshold: float
    normalized_risk_bound: float
    assumptions: tuple[str, ...]
    valid_for_case: bool


class EvidenceAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str
    evidence_id: str
    acquisition_cost: int = Field(ge=0)
    policy_id: str
    reason: str


class CarveDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    status: DecisionStatus
    reason_code: str
    proof: InvariantResult
    risk: RiskPrediction | None = None
    risk_certificate: RiskCertificate | None = None
    next_evidence: EvidenceAction | None = None
    razorpay_write_performed: Literal[False] = False


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def evidence_digest(artifact: EvidenceArtifact) -> str:
    raw = (
        artifact.content
        + "\n"
        + json.dumps(
            artifact.structured_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def _value(value: Any) -> z3.ArithRef | z3.SeqRef | z3.BoolRef:
    if isinstance(value, bool):
        return z3.BoolVal(value)
    if isinstance(value, int):
        return z3.IntVal(value)
    return z3.StringVal(str(value))


def _new_solver() -> z3.Solver:
    solver = z3.Solver()
    solver.set("timeout", SOLVER_TIMEOUT_MS)
    return solver


def _minimize_unsat(
    assertions: list[tuple[str, z3.BoolRef]],
) -> tuple[list[tuple[str, z3.BoolRef]], bool]:
    selected = list(assertions)
    changed = True
    proved_minimal = True
    while changed:
        changed = False
        for item in list(selected):
            trial = [candidate for candidate in selected if candidate is not item]
            solver = _new_solver()
            solver.add([expression for _, expression in trial])
            result = solver.check()
            if result == z3.unsat:
                selected = trial
                changed = True
                break
            if result == z3.unknown:
                proved_minimal = False
    return selected, proved_minimal


def _proof(
    case_id: str,
    invariant_id: str,
    claim: GroundedClaim,
    claim_field: str,
    claim_value: Any,
    authoritative_field: str,
    authoritative_value: Any,
    authoritative_evidence: str,
    invariant_expression: Any,
) -> InvariantResult:
    claim_var = z3.Const(f"claim_{claim_field}", _value(claim_value).sort())
    authority_var = z3.Const(f"authority_{authoritative_field}", _value(authoritative_value).sort())
    assertions = [
        ("claim", claim_var == _value(claim_value)),
        ("authority", authority_var == _value(authoritative_value)),
        ("invariant", invariant_expression(claim_var, authority_var)),
    ]
    solver = _new_solver()
    labels: dict[str, z3.BoolRef] = {}
    for name, expression in assertions:
        label = z3.Bool(f"track_{name}")
        labels[name] = label
        solver.assert_and_track(expression, label)
    result = solver.check()
    if result == z3.sat:
        return InvariantResult(
            case_id=case_id,
            status="SAT",
            invariant_id=invariant_id,
            reason="Compiled supported invariant is satisfiable.",
        )
    if result == z3.unknown:
        return InvariantResult(
            case_id=case_id,
            status="ERROR",
            invariant_id=invariant_id,
            reason=f"Bounded solver did not decide the invariant: {solver.reason_unknown()}.",
        )
    core_names = {name for name, label in labels.items() if label in set(solver.unsat_core())}
    minimized, proved_minimal = _minimize_unsat(
        [item for item in assertions if item[0] in core_names]
    )
    minimized_names = {name for name, _ in minimized}
    facts = []
    if "claim" in minimized_names:
        facts.append(
            ProofFact(
                fact_id=f"{claim.claim_id}:{claim_field}",
                kind="GROUNDED_CLAIM",
                field=claim_field,
                value=claim_value,
                evidence_id=claim.source_document,
                source_span=claim.source_span,
            )
        )
    if "authority" in minimized_names:
        facts.append(
            ProofFact(
                fact_id=f"{authoritative_evidence}:{authoritative_field}",
                kind="AUTHORITATIVE_FACT",
                field=authoritative_field,
                value=authoritative_value,
                evidence_id=authoritative_evidence,
            )
        )
    if "invariant" in minimized_names:
        facts.append(
            ProofFact(
                fact_id=f"invariant:{invariant_id}",
                kind="INVARIANT",
                field=invariant_id,
                value="REQUIRED",
            )
        )
    proof_payload = {
        "case_id": case_id,
        "invariant_id": invariant_id,
        "facts": [fact.model_dump(mode="json") for fact in facts],
    }
    evidence_ids = tuple(
        sorted({fact.evidence_id for fact in facts if fact.evidence_id is not None})
    )
    certificate = ContradictionCertificate(
        certificate_id=f"mcc:{case_id}",
        case_id=case_id,
        invariant_id=invariant_id,
        facts=tuple(facts),
        evidence_ids=evidence_ids,
        minimal_relative_to_compiled_constraints=proved_minimal,
        proof_sha256=hashlib.sha256(canonical(proof_payload)).hexdigest(),
    )
    return InvariantResult(
        case_id=case_id,
        status="UNSAT",
        invariant_id=invariant_id,
        certificate=certificate,
        reason="Grounded claim and authoritative fact violate a compiled financial invariant.",
    )


def _incomplete(case_id: str, missing: list[str], reason: str) -> InvariantResult:
    return InvariantResult(
        case_id=case_id,
        status="INCOMPLETE",
        invariant_id=None,
        missing_evidence=tuple(sorted(missing)),
        reason=reason,
    )


def compile_financial_proof(row: dict[str, Any], visible_evidence_ids: set[str]) -> InvariantResult:
    """Compile only visible, digest-valid evidence. Hidden benchmark truth is never consulted."""
    case_id = str(row["case_id"])
    if row.get("ood_type") is not None or row.get("authoritative_state") is None:
        return _incomplete(case_id, [], "OOD or missing authoritative state requires REVIEW.")
    inventory = {
        artifact.evidence_id: artifact
        for item in row["complete_evidence_inventory"]
        if (artifact := EvidenceArtifact.model_validate(item)).evidence_id in visible_evidence_ids
    }
    corrupt = [
        artifact.evidence_id
        for artifact in inventory.values()
        if evidence_digest(artifact) != artifact.content_sha256
    ]
    if corrupt:
        return _incomplete(case_id, corrupt, "Evidence digest mismatch requires REVIEW.")
    if "customer_communication" not in inventory:
        return _incomplete(
            case_id, ["customer_communication"], "Grounded communication is unavailable."
        )
    claim = GroundedClaim.model_validate(row["atomic_claims"][0])
    document = inventory[claim.source_document].content
    start, end = claim.source_span
    if not claim.grounded or document[start:end] != claim.source_quote:
        return _incomplete(case_id, [], "Exact claim grounding failed.")
    attrs = claim.attributes
    quote = claim.source_quote
    relation = claim.relation

    def equality(
        invariant: str,
        claim_field: str,
        claim_value: Any,
        authority_field: str,
        authority_value: Any,
        evidence_id: str,
    ) -> InvariantResult:
        return _proof(
            case_id,
            invariant,
            claim,
            claim_field,
            claim_value,
            authority_field,
            authority_value,
            evidence_id,
            lambda left, right: left == right,
        )

    # Invariant applicability is derived from the grounded claim, never benchmark labels,
    # phenomenon names, expected constraints, or oracle acquisition annotations.
    missing: set[str] = set()
    checks: list[InvariantResult] = []

    refund_state = inventory.get("refund_state")
    refund: dict[str, Any] | None = None
    refunds: list[dict[str, Any]] = []
    if relation in {"CLAIMS_REFUND_PROCESSED", "PROMISES_REFUND"}:
        if refund_state is None:
            missing.add("refund_state")
        else:
            refunds = list(refund_state.structured_payload.get("refunds", []))
            if not refunds:
                return _incomplete(case_id, [], "Authoritative refund export contains no record.")
            refund = refunds[0]

    if refund is not None:
        claim_amount = int(attrs["amount_minor"])
        cumulative_refund = sum(int(item["amount_minor"]) for item in refunds)
        payment_amount = int(row["authoritative_state"]["payment"]["amount_minor"])
        amount_invariant = (
            "CUMULATIVE_AMOUNT"
            if len(refunds) > 1 or claim_amount == payment_amount != cumulative_refund
            else "AMOUNT_EQUALITY"
        )
        checks.append(
            equality(
                amount_invariant,
                "amount_minor",
                claim_amount,
                "cumulative_refund_minor",
                cumulative_refund,
                "refund_state",
            )
        )
        checks.append(
            equality(
                "CURRENCY_EQUALITY",
                "currency",
                attrs["currency"],
                "currency",
                refund["currency"],
                "refund_state",
            )
        )
        if str(attrs.get("refund_id", "")) in quote:
            checks.append(
                equality(
                    "REFUND_IDENTITY",
                    "refund_id",
                    attrs["refund_id"],
                    "refund_id",
                    refund["refund_id"],
                    "refund_state",
                )
            )
        if str(attrs.get("payment_id", "")) in quote:
            checks.append(
                equality(
                    "PAYMENT_PARENT_IDENTITY",
                    "payment_id",
                    attrs["payment_id"],
                    "parent_payment_id",
                    refund["parent_payment_id"],
                    "refund_state",
                )
            )
        if relation == "CLAIMS_REFUND_PROCESSED":
            claim_status = str(attrs.get("refund_status", "processed"))
            if claim_status != "processed":
                checks.append(
                    equality(
                        "REFUND_STATUS",
                        "refund_status",
                        claim_status,
                        "refund_status",
                        refund["status"],
                        "refund_state",
                    )
                )
            else:
                checks.append(
                    equality(
                        "CLAIM_POLARITY",
                        "claim_affirms_processed",
                        not bool(attrs.get("negated", False)),
                        "refund_is_processed",
                        refund["status"] == "processed",
                        "refund_state",
                    )
                )
            claim_date = str(attrs.get("claim_date", ""))
            if claim_date and claim_date in quote:
                checks.append(
                    _proof(
                        case_id,
                        "TEMPORAL_ORDER",
                        claim,
                        "claim_date_ordinal",
                        date.fromisoformat(claim_date).toordinal(),
                        "refund_created_ordinal",
                        date.fromisoformat(str(refund["created_at"])).toordinal(),
                        "refund_state",
                        lambda left, right: left >= right,
                    )
                )
        elif relation == "PROMISES_REFUND":
            assert refund_state is not None
            due_day = date.fromisoformat(str(attrs["due_date"])).toordinal()
            as_of = date.fromisoformat(str(refund_state.structured_payload["as_of"])).toordinal()
            checks.append(
                _proof(
                    case_id,
                    "PROMISE_DEADLINE",
                    claim,
                    "promise_not_overdue",
                    due_day >= as_of,
                    "refund_processed",
                    refund["status"] == "processed",
                    "refund_state",
                    lambda not_overdue, processed: z3.Or(not_overdue, processed),
                )
            )

    rrn = str(attrs.get("rrn", ""))
    if rrn and rrn in quote:
        if "rrn_linkage" not in inventory:
            missing.add("rrn_linkage")
        else:
            payload = inventory["rrn_linkage"].structured_payload
            checks.append(
                equality("RRN_PARENT_LINK", "rrn", rrn, "rrn", payload["rrn"], "rrn_linkage")
            )

    arn_utr = str(attrs.get("arn_utr", ""))
    if arn_utr and arn_utr in quote:
        if "completion_reference" not in inventory:
            missing.add("completion_reference")
        else:
            payload = inventory["completion_reference"].structured_payload
            checks.append(
                equality(
                    "COMPLETION_REFERENCE",
                    "arn_utr",
                    arn_utr,
                    "arn_utr",
                    payload["arn_utr"],
                    "completion_reference",
                )
            )

    order_id = str(attrs.get("order_id", ""))
    if order_id and order_id in quote:
        if "order_record" not in inventory:
            missing.add("order_record")
        else:
            payload = inventory["order_record"].structured_payload
            checks.append(
                equality(
                    "ORDER_IDENTITY",
                    "order_id",
                    order_id,
                    "order_id",
                    payload["order_id"],
                    "order_record",
                )
            )

    if "refund eligible" in quote.lower():
        if "refund_policy" not in inventory:
            missing.add("refund_policy")
        else:
            checks.append(
                equality(
                    "POLICY_ELIGIBILITY",
                    "claim_requires_eligible_policy",
                    True,
                    "return_eligible",
                    inventory["refund_policy"].structured_payload["return_eligible"],
                    "refund_policy",
                )
            )

    contradiction = next((result for result in checks if result.status == "UNSAT"), None)
    if contradiction is not None:
        return contradiction
    solver_error = next((result for result in checks if result.status == "ERROR"), None)
    if solver_error is not None:
        return solver_error
    if missing:
        return _incomplete(
            case_id, sorted(missing), "Applicable invariant evidence is not visible."
        )
    if not checks:
        return _incomplete(case_id, [], "No supported grounded financial invariant was applicable.")
    return InvariantResult(
        case_id=case_id,
        status="SAT",
        invariant_id="COMPILED_FINANCIAL_INVARIANTS",
        reason=f"All {len(checks)} applicable compiled financial invariants are satisfiable.",
    )


def apply_hard_precedence(
    proof: InvariantResult,
    risk: RiskPrediction | None,
    risk_certificate: RiskCertificate | None,
) -> CarveDecision:
    """Return a decision while making hard safety precedence explicit and testable."""
    if proof.status == "UNSAT":
        return CarveDecision(
            case_id=proof.case_id,
            status=DecisionStatus.BLOCK,
            reason_code="F_FORMAL_FINANCIAL_CONTRADICTION",
            proof=proof,
            risk=risk,
            risk_certificate=risk_certificate,
        )
    if proof.status != "SAT":
        return CarveDecision(
            case_id=proof.case_id,
            status=DecisionStatus.REVIEW,
            reason_code="F_VERIFICATION_INCOMPLETE",
            proof=proof,
            risk=risk,
            risk_certificate=risk_certificate,
        )
    if risk is None or risk_certificate is None or not risk_certificate.valid_for_case:
        return CarveDecision(
            case_id=proof.case_id,
            status=DecisionStatus.REVIEW,
            reason_code="F_RISK_CERTIFICATE_UNAVAILABLE",
            proof=proof,
            risk=risk,
            risk_certificate=risk_certificate,
        )
    if risk.residual_risk <= risk_certificate.pass_threshold:
        return CarveDecision(
            case_id=proof.case_id,
            status=DecisionStatus.PASS,
            reason_code="NO_SUPPORTED_INTEGRITY_ISSUE",
            proof=proof,
            risk=risk,
            risk_certificate=risk_certificate,
        )
    return CarveDecision(
        case_id=proof.case_id,
        status=DecisionStatus.REVIEW,
        reason_code="F_RESIDUAL_RISK_ABSTENTION",
        proof=proof,
        risk=risk,
        risk_certificate=risk_certificate,
    )


def point_in_time_snapshot(row: dict[str, Any], decision_time: str) -> dict[str, Any]:
    """Point-in-time evidence snapshot ensuring no look-ahead leakage.

    Only evidence items where available_time <= decision_time are visible.
    """
    snapshot = copy.deepcopy(row)
    try:
        decision_at = datetime.fromisoformat(decision_time.replace("Z", "+00:00"))
        if decision_at.tzinfo is None:
            raise ValueError("decision_time must include a timezone")
        decision_at = decision_at.astimezone(timezone.utc)
    except (TypeError, ValueError) as error:
        raise ValueError(
            "decision_time must be a valid timezone-aware ISO-8601 timestamp"
        ) from error
    visible_inventory: list[dict[str, Any]] = []
    for item in snapshot.get("complete_evidence_inventory", []):
        # Invariant: Evidence without valid temporal provenance is strictly excluded (fail closed)
        avail = item.get("available_time") or item.get("ingested_at")
        if not isinstance(avail, str):
            continue
        try:
            available_at = datetime.fromisoformat(avail.replace("Z", "+00:00"))
            if available_at.tzinfo is None:
                continue
            available_at = available_at.astimezone(timezone.utc)
        except ValueError:
            continue
        if available_at <= decision_at:
            visible_inventory.append(item)
    snapshot["complete_evidence_inventory"] = visible_inventory
    return snapshot


class AutomationRiskBudget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    daily_risk_budget: float = 100.0  # Max acceptable economic loss exposure
    consumed_risk: float = 0.0
    daily_review_capacity: int = 500
    review_count: int = 0
    circuit_breaker_state: CircuitBreakerState = CircuitBreakerState.AUTOMATION_ENABLED

    def can_automate(
        self,
        estimated_error_prob: float,
        economic_loss_if_wrong: float = 10.0,
    ) -> bool:
        if self.circuit_breaker_state == CircuitBreakerState.REVIEW_ONLY:
            return False
        case_risk = estimated_error_prob * economic_loss_if_wrong
        return (self.consumed_risk + case_risk) <= self.daily_risk_budget

    def record_decision(
        self,
        decision: DecisionStatus,
        estimated_error_prob: float,
        economic_loss_if_wrong: float = 10.0,
    ) -> None:
        if decision == DecisionStatus.REVIEW:
            self.review_count += 1
            if self.review_count >= self.daily_review_capacity:
                self.circuit_breaker_state = CircuitBreakerState.DEGRADED
        else:
            self.consumed_risk += estimated_error_prob * economic_loss_if_wrong
            if self.consumed_risk >= self.daily_risk_budget:
                self.circuit_breaker_state = CircuitBreakerState.REVIEW_ONLY


SOLVER_TIMEOUT_MS = 50
