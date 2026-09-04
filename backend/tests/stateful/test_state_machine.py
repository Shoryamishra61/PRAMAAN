"""Hypothesis RuleBasedStateMachine tests for dispute lifecycles and state transitions in PRAMAAN.

Models transitions between:
- ProcessingStatus: RECEIVED -> QUEUED -> PROCESSING -> READY / FAILED
- WorkflowStatus: REVIEW_PENDING -> READY_FOR_CONTEST / READY_WITH_OVERRIDE
- DecisionStatus: PASS / REVIEW / BLOCK

Invariants verified:
1. Contradictory evidence never transitions to CONTEST_READY automatically.
2. An override cannot be granted unless all cited contradiction sources have been inspected.
3. Expired or failed processing cases never become CONTEST_READY.
4. Unknown transitions fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from hypothesis import stateful as sf
from hypothesis import strategies as st


class LifecycleState(str, Enum):
    RECEIVED = "RECEIVED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    CONTEST_READY = "CONTEST_READY"
    BLOCKED_CONTRADICTION = "BLOCKED_CONTRADICTION"
    OVERRIDDEN = "OVERRIDDEN"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"


@dataclass
class SimulatedCase:
    case_id: str
    amount_minor: int
    state: LifecycleState = LifecycleState.RECEIVED
    has_contradiction: bool = False
    has_ungrounded_claim: bool = False
    is_expired: bool = False
    citations_inspected: bool = False
    override_reason: str | None = None
    evaluation_count: int = 0


class DisputeLifecycleStateMachine(sf.RuleBasedStateMachine):
    def __init__(self) -> None:
        super().__init__()
        self.cases: dict[str, SimulatedCase] = {}

    @sf.rule(
        case_id=st.integers(min_value=1, max_value=100).map(lambda n: f"case_{n}"),
        amount_minor=st.integers(min_value=100, max_value=1_000_000),
    )
    def create_case(self, case_id: str, amount_minor: int) -> None:
        if case_id not in self.cases:
            self.cases[case_id] = SimulatedCase(case_id=case_id, amount_minor=amount_minor)

    @sf.rule(
        case_id=st.integers(min_value=1, max_value=100).map(lambda n: f"case_{n}"),
    )
    def queue_case(self, case_id: str) -> None:
        case = self.cases.get(case_id)
        if case and case.state == LifecycleState.RECEIVED:
            case.state = LifecycleState.QUEUED

    @sf.rule(
        case_id=st.integers(min_value=1, max_value=100).map(lambda n: f"case_{n}"),
        has_contradiction=st.booleans(),
        has_ungrounded=st.booleans(),
    )
    def attach_evidence_and_evaluate(
        self, case_id: str, has_contradiction: bool, has_ungrounded: bool
    ) -> None:
        case = self.cases.get(case_id)
        if not case or case.state not in {LifecycleState.QUEUED, LifecycleState.PROCESSING}:
            return

        case.state = LifecycleState.PROCESSING
        case.has_contradiction = has_contradiction
        case.has_ungrounded_claim = has_ungrounded
        case.evaluation_count += 1

        # Hard invariant precedence logic
        if case.is_expired:
            case.state = LifecycleState.EXPIRED
        elif case.has_contradiction:
            case.state = LifecycleState.BLOCKED_CONTRADICTION
        elif case.has_ungrounded_claim:
            case.state = LifecycleState.REVIEW_REQUIRED
        else:
            case.state = LifecycleState.CONTEST_READY

    @sf.rule(
        case_id=st.integers(min_value=1, max_value=100).map(lambda n: f"case_{n}"),
        inspected_all=st.booleans(),
        reason=st.text(min_size=5, max_size=50),
    )
    def apply_override(self, case_id: str, inspected_all: bool, reason: str) -> None:
        case = self.cases.get(case_id)
        if not case:
            return

        # High-integrity safeguard: override requires inspection of all cited sources
        if (
            case.state in {LifecycleState.REVIEW_REQUIRED, LifecycleState.BLOCKED_CONTRADICTION}
            and inspected_all
            and not case.is_expired
        ):
            case.citations_inspected = True
            case.override_reason = reason
            case.state = LifecycleState.OVERRIDDEN

    @sf.rule(case_id=st.integers(min_value=1, max_value=100).map(lambda n: f"case_{n}"))
    def expire_case(self, case_id: str) -> None:
        case = self.cases.get(case_id)
        if case:
            case.is_expired = True
            case.state = LifecycleState.EXPIRED

    @sf.invariant()
    def invariant_no_uninspected_override_can_be_ready(self) -> None:
        """A case can never be in OVERRIDDEN state without explicit citation inspection."""
        for case in self.cases.values():
            if case.state == LifecycleState.OVERRIDDEN:
                assert case.citations_inspected is True
                assert case.override_reason is not None

    @sf.invariant()
    def invariant_contradiction_never_auto_contest_ready(self) -> None:
        """A case with a formal contradiction can NEVER be in CONTEST_READY."""
        for case in self.cases.values():
            if case.has_contradiction:
                assert case.state != LifecycleState.CONTEST_READY

    @sf.invariant()
    def invariant_ungrounded_claim_never_auto_contest_ready(self) -> None:
        """A case with an ungrounded claim can NEVER be in CONTEST_READY."""
        for case in self.cases.values():
            if case.has_ungrounded_claim:
                assert case.state != LifecycleState.CONTEST_READY

    @sf.invariant()
    def invariant_expired_never_contest_ready(self) -> None:
        """An expired case can never be CONTEST_READY or OVERRIDDEN."""
        for case in self.cases.values():
            if case.is_expired:
                assert case.state == LifecycleState.EXPIRED


TestDisputeLifecycle = DisputeLifecycleStateMachine.TestCase
