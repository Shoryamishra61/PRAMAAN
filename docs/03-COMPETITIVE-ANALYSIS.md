# 03 — Competitive Analysis & Differentiation

## Evidence standard

This document compares **publicly documented capabilities**, not private product internals. “Not documented” does not mean “does not exist.”

## Publicly documented adjacent products

### Stripe Smart Disputes
Public documentation describes automatic evidence submission for eligible disputes and auto-response configuration. [SRC-COMP-02]

### Justt
Public material describes:
- evidence enrichment from merchant/third-party data;
- dynamic argument generation;
- automated representment;
- reason-code/issuer/card-scheme aware optimization;
- A/B testing and recovery optimization. [SRC-COMP-03]

### Chargeflow
Current public API/docs describe:
- dispute ingestion;
- evidence enrichment/upload;
- AI-built evidence packages;
- automatic representment submission. [SRC-COMP-04]

## Safe competitive claim

Allowed:
> “The public materials we reviewed emphasize evidence collection, enrichment, argument construction and automated submission. We did not find public documentation describing a standalone merchant-side pre-submission gate whose primary artifact is an auditable cross-source inconsistency report with grounded source spans.”

Not allowed:
> “No competitor checks contradictions.”
> “We are the first.”
> “Incumbents blindly submit evidence.”

## Differentiation axes

1. **Verifier, not generator**  
   The product creates no representment prose.

2. **Grounded semantic extraction**  
   Every AI-derived material claim must point to exact source text.

3. **Structured-system reconciliation**  
   Semantic claims are checked against trusted refund/payment records using code.

4. **Safe abstention**  
   Missing/ungrounded/unsupported semantics produce REVIEW, not a guess.

5. **Evaluation-first product surface**  
   The project exposes reproducible held-out precision/recall and error slices.

6. **Human decision-quality UX**  
   The UI makes the evidence conflict inspectable before an override.

## Saturation risks

Likely crowded/obvious Track 02 categories:
- generic transaction fraud classifier;
- Kaggle fraud model;
- chargeback letter generator;
- risk chatbot;
- reason-code RAG;
- generic “AI risk score”.

The Dispute Integrity Gate should never drift toward these.

## Judge answer: “Why not use the existing chargeback automation platform?”

> “Those products solve evidence acquisition, argument construction and submission. Our build explores a different control point: whether a merchant can independently verify the internal supportability of a draft packet before human submission. The differentiator is not that other platforms are bad; it is that verification is independently measurable, auditable and separable from generation.”

## Defensibility

Hackathon defensibility comes from:
- exact Razorpay workflow integration;
- reason-profile rules;
- benchmark/evaluation harness;
- typed evidence ontology;
- grounded audit UX;
- explicit safe-failure semantics.

It does not come from proprietary model IP or unsupported “first ever” claims.
