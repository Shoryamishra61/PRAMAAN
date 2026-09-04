# Problem decomposition

**Scope:** Razorpay AI Buildathon Track 02, one loss class selected: refund/credit-not-processed evidence-integrity failures.

## Decision

- **FACT:** Razorpay describes RZP04 as a case where a business promised a refund but did not process it, and lists refund-generation proof, amount-matching bank evidence, customer communication, and refund policies as suggested evidence. [Razorpay evidence guide](https://razorpay.com/docs/payments/disputes/submit-evidence/)
- **DESIGN DECISION:** The product remains a defensive, read-only pre-submission verifier for `refund_not_processed_v1`; it does not become a general fraud scorer, representment writer, or autonomous refund/contest system.
- **RESEARCH RESULT:** The frozen v1 study showed that semantic models recover unseen wording but also confuse approval/obligation with completed refund claims; neither learned extractor met the existing safety gate. See `artifacts/research/ai-systems-study-v1.md`.
- **HYPOTHESIS:** The remaining tractable loss is avoidable representment failure caused by contradictions or incompleteness inside the merchant's own evidence packet.

## Track-wide loss ontology

| Loss type | Monetary cause | Signal generator | Intervention point | Observable / latent | Realistic label | FP / FN / abstention cost | Commercial maturity | Human residue | Rule failure | Plausible ML lift |
|---|---|---|---|---|---|---|---|---|---|---|
| Third-party payment fraud | **FACT:** Unauthorized purchase becomes goods loss, chargeback, fee, or decline cost. | **FACT:** payment, device, identity, authentication and network events. | **DESIGN DECISION:** pre-authorization or pre-fulfilment. | **FACT:** device/velocity are observable; intent is latent. | **ASSUMPTION:** confirmed issuer fraud outcome after delay. | **ASSUMPTION:** false block loses a good sale; false pass loses goods and fees. | **INDUSTRY CLAIM:** mature network-scale scoring is sold by Razorpay, Stripe, Visa, Riskified, Signifyd and others. | **FACT:** edge cases and appeals remain. | **HYPOTHESIS:** adaptive camouflage and cross-entity relations. | **HYPOTHESIS:** temporal/graph representation when real entity edges exist. |
| First-party/friendly fraud | **FACT:** a legitimate purchaser disputes a legitimate transaction. | **FACT:** order, account, delivery, usage and historical transaction data. | **DESIGN DECISION:** pre-dispute deflection or representment. | **FACT:** fulfilment is observable; cardholder intent is latent. | **ASSUMPTION:** final dispute outcome is an imperfect proxy. | **ASSUMPTION:** accusation harms good customers; missed abuse loses sale and goods. | **INDUSTRY CLAIM:** Visa CE3.0, Order Insight and commercial recovery products address it. | **FACT:** policy/context judgement remains. | **HYPOTHESIS:** dispersed historical evidence and issuer-specific interactions. | **HYPOTHESIS:** relational history models, but only with network-scale data. |
| Chargeback abuse | **FACT:** repeated invalid disputes create refund, goods, fee and operational loss. | **FACT:** dispute history, user/order/device links and outcomes. | **DESIGN DECISION:** pre-dispute or representment selection. | **FACT:** repeated patterns are observable; malicious intent is latent. | **ASSUMPTION:** domain-reviewed abusive/non-abusive outcome. | **ASSUMPTION:** false accusation is high-cost; abstention consumes analyst time. | **INDUSTRY CLAIM:** mature recovery and guarantee products exist. | **FACT:** ambiguous customer-service facts remain. | **HYPOTHESIS:** static thresholds miss coordinated or evolving behavior. | **HYPOTHESIS:** graph/temporal models if genuine repeated-entity data is available. |
| Refund abuse | **FACT:** duplicate, inflated or policy-ineligible refunds cause direct loss. | **FACT:** order, return, refund and customer-support events. | **DESIGN DECISION:** before refund approval or before dispute evidence submission. | **FACT:** ledger values are observable; intent and off-platform activity may be latent. | **ASSUMPTION:** adjudicated refund eligibility and final refund state. | **ASSUMPTION:** false block harms service; false pass loses cash. | **INDUSTRY CLAIM:** rule and risk platforms cover parts of this workflow. | **FACT:** exception policy remains human. | **HYPOTHESIS:** paraphrased promises and cross-channel contradictions. | **HYPOTHESIS:** grounded semantic extraction, not learned arithmetic. |
| Return abuse | **INDUSTRY CLAIM:** empty-box, wrong-item, wardrobing or repeated returns consume goods, shipping and handling. | **FACT:** order, warehouse, carrier, image and account history. | **DESIGN DECISION:** return authorization, receipt or refund. | **FACT:** scans/photos observable; intent and item substitution can be latent. | **ASSUMPTION:** warehouse-verified condition/outcome. | **ASSUMPTION:** false block harms retention; false pass loses inventory. | **INDUSTRY CLAIM:** established ecommerce abuse products exist. | **FACT:** physical inspection remains. | **HYPOTHESIS:** multi-modal ambiguity and sparse labels. | **HYPOTHESIS:** vision/sequence models only with real inspection data. |
| Evidence-quality failure | **FACT:** missing, unreadable, mismatched or contradictory evidence weakens a dispute response. | **FACT:** merchant documents, communications and authoritative transaction/refund state. | **DESIGN DECISION:** immediately before human submission. | **FACT:** packet contents and ledger are observable; issuer interpretation is latent. | **DESIGN DECISION:** atomic integrity findings plus `PASS/REVIEW/BLOCK`. | **ASSUMPTION:** false PASS risks bad submission; false BLOCK delays a valid response; REVIEW costs analyst time. | **INDUSTRY CLAIM:** evidence assembly is commoditized; public evidence of pre-submit contradiction debugging is limited. | **FACT:** repair and final submission remain human. | **HYPOTHESIS:** exact but paraphrased claims defeat lexical rules. | **HYPOTHESIS:** grounded claim extraction and relation classification. |
| Representment failure | **FACT:** missed deadline, wrong reason evidence or weak packet can cause loss. | **FACT:** dispute metadata, evidence inventory, submission and issuer outcome. | **DESIGN DECISION:** before submission and before deadline. | **FACT:** deadline/completeness observable; issuer decision latent. | **ASSUMPTION:** accepted/rejected and won/lost outcomes, carefully time-stamped. | **ASSUMPTION:** unnecessary contesting adds cost; missed valid contest loses recovery. | **INDUSTRY CLAIM:** Stripe, Chargeflow, Justt, Forter and Signifyd automate this. | **FACT:** responsibility for source accuracy remains with merchant/operator. | **HYPOTHESIS:** policy variation and missing cross-system data. | **HYPOTHESIS:** retrieval/ranking can help only when policy corpus is authoritative and versioned. |
| Fraud spikes | **FACT:** a rapid change can overwhelm static controls. | **FACT:** streaming aggregate rates and outcomes. | **DESIGN DECISION:** monitoring and pre-authorization. | **FACT:** rate change observable; root cause initially latent. | **ASSUMPTION:** incident-confirmed window. | **ASSUMPTION:** false alarms create operational load; misses create concentrated loss. | **INDUSTRY CLAIM:** processors sell real-time risk monitoring. | **FACT:** incident triage remains. | **HYPOTHESIS:** fixed thresholds ignore seasonality and drift. | **HYPOTHESIS:** change-point/temporal anomaly detection. |
| Coordinated abuse rings | **FACT:** linked actors distribute behavior across accounts/devices/orders. | **FACT:** entity and event relationships. | **DESIGN DECISION:** pre-fulfilment or investigation. | **FACT:** edges partly observable; organization is latent. | **ASSUMPTION:** investigation-confirmed entities/subgraphs. | **ASSUMPTION:** false association can block innocent shared infrastructure. | **INDUSTRY CLAIM:** graph fraud detection is established research and practice. | **FACT:** investigator validation remains. | **HYPOTHESIS:** independent rows discard topology. | **HYPOTHESIS:** GNN/community methods when stable entity edges exist. |
| Policy abuse / operational mistakes | **FACT:** inconsistent policy enforcement, duplicate actions, wrong amounts and stale communications create avoidable loss. | **FACT:** policy versions, workflow events, ledger and communications. | **DESIGN DECISION:** before irreversible human action. | **FACT:** recorded state is observable; undocumented exceptions are latent. | **ASSUMPTION:** root-cause-reviewed incident labels. | **ASSUMPTION:** false hard stops delay customers; misses create direct loss. | **INDUSTRY CLAIM:** workflow and rules tooling is common. | **FACT:** exception approval remains human. | **HYPOTHESIS:** rules cannot interpret messy communication reliably. | **HYPOTHESIS:** grounded extraction plus deterministic invariants. |

## Causal chain and failure tree

**FACT:** Customer communication can assert that a refund was processed while the authoritative refund export has no matching completed entry.

```text
support promise or status message
  -> semantic claim enters evidence packet
  -> claim is not reconciled to complete refund ledger
  -> packet is submitted as internally consistent
  -> issuer requests more information or rejects evidence
  -> merchant loses recoverable value and analyst time
```

**DESIGN DECISION:** The system intervenes only between packet assembly and a human submission decision.

```text
Bad packet
├─ structured evidence incomplete -> REVIEW
├─ input unsupported/malformed -> no decision or REVIEW
├─ claim cannot be uniquely grounded -> REVIEW
├─ model unavailable/OOD/disagrees -> REVIEW
└─ grounded material claim contradicts complete authoritative ledger -> BLOCK
```

## JTBD and opportunity

- **DESIGN DECISION:** When preparing a refund-not-processed response, help a merchant-risk analyst locate the exact sentence that creates a financial assertion, test it against authoritative refund state, and repair the packet before any external action.
- **HYPOTHESIS:** The judge-visible value is causal debugging, not a risk score: corrupt one fact, observe the finding and safe state change, repair the fact, then observe the decision diff.
- **DESIGN DECISION:** The opportunity excludes transaction-fraud scoring, customer intent inference, automated representment, and issuer win prediction because those are data-inaccessible, commercially mature, or outside the defense-only safety boundary.

