# 02 — Problem Validation & Service Boundary

## Validated workflow facts

Razorpay disputes have:
- `payment.dispute.created` and later lifecycle webhook events;
- `respond_by`, `status`, `phase`, `reason_code`, and evidence fields;
- documented contest and accept APIs;
- `payment.dispute.action_required`, described for cases where submitted evidence is insufficient, unreadable, or does not correspond to the contested amount. [SRC-RZP-02, SRC-RZP-04, SRC-RZP-07]

Razorpay's evidence guide lists reason-specific suggested evidence, including refund proof, timestamps, customer communication and policies for refund-not-processed categories. [SRC-RZP-06]

These primary facts support a narrower thesis than the original reports:
> **Evidence quality and correspondence are operationally relevant. A pre-submission merchant-side verifier can be tested against whether a draft packet is internally supportable before the merchant chooses to contest.**

## What is not proven

The research did **not** establish:
- how often real merchant packets contain semantic contradictions;
- that contradictions directly cause a specific percentage of losses;
- that current vendors never perform consistency checks internally;
- a real merchant ROI percentage;
- a real analyst reviewing exactly N cases/day.

These remain hypotheses and must not be pitched as facts.

## Primary user

**Dispute operations analyst** (generic role, not a claimed Razorpay persona).

JTBD:
> “Before I mark a refund-not-processed dispute packet ready to contest, help me verify that the refund facts, customer communication, and structured transaction state agree—and show me the exact evidence when they do not.”

## Buyer/stakeholders

Hypothesized deployment stakeholders:
- merchant risk/dispute operations;
- payments engineering/integrations;
- finance/risk leadership.

Razorpay, issuer banks, and card schemes remain external workflow participants, not users of the MVP.

## Current-state journey

1. dispute is created;
2. merchant is notified;
3. evidence is gathered;
4. merchant may draft evidence;
5. merchant chooses whether to accept or contest;
6. issuer reviews submitted evidence;
7. Razorpay may emit lifecycle/action-required events.

The MVP inserts a checkpoint between **evidence draft** and **human contest decision**.

## Root-cause hypothesis

Not: “analysts are careless.”

More defensible:
1. evidence originates from heterogeneous systems;
2. evidence assembly and evidence consistency are different tasks;
3. structured refund state and unstructured customer communication can disagree;
4. under time pressure, manually verifying every cross-source claim is expensive;
5. therefore a grounded integrity verifier may reduce avoidable review errors.

## MVP problem family

**Refund / Credit Not Processed**

Why:
- directly represented in Razorpay evidence guidance (RZP04 and Visa 13.6 examples); [SRC-RZP-06]
- naturally combines structured refund state with unstructured communication;
- supports meaningful AI extraction without asking AI to perform financial arithmetic;
- easy to produce deterministic synthetic ground truth.

## Non-goals

Do not:
- judge the cardholder's truthfulness;
- label “friendly fraud”;
- decide dispute outcome;
- infer card-network law;
- calculate win probability;
- automatically accept/contest;
- browse merchant systems autonomously.

## Falsification conditions

The product thesis weakens materially if:
1. a strong deterministic/regex baseline performs equivalently on the semantic benchmark;
2. grounded extraction errors create excessive false holds;
3. the verifier cannot identify conflicts without broad, subjective policy interpretation;
4. end-to-end semantic latency prevents useful pre-processing before analyst review;
5. competitor/public product research reveals the exact same standalone workflow with no meaningful differentiation.

No fixed “5% F1” kill threshold is predeclared without uncertainty analysis. Report effect size and uncertainty; retain complexity only when value is operationally meaningful and visible.
