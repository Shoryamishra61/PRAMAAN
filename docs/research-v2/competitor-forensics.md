# Competitor forensics

## Public capability map

| Provider | Ingestion -> features -> model | Decision / evidence / automation | Human / feedback / metrics | Whitespace implication |
|---|---|---|---|---|
| **INDUSTRY CLAIM:** [Stripe Smart Disputes](https://docs.stripe.com/disputes/smart-disputes) | Stripe transaction, cardholder, network and merchant data -> stated AI rules engine | eligibility -> tailored evidence packet -> optional automatic submission | merchant remains responsible for accuracy; issuer decides; public product describes fee-on-win | Evidence assembly and auto-submit are commoditized. |
| **INDUSTRY CLAIM:** [Chargeflow](https://docs.chargeflow.io/docs/reference/concepts/dispute-automation) | PSP disputes + merchant enrichment + historical/network/domain signals -> agentic engine | strategy, generated response and automatic submission | outcome flows into later cases; win-rate claims are vendor claims | Agentic representment is crowded and outside our boundary. |
| **INDUSTRY CLAIM:** [Justt](https://justt.ai/platform/) | merchant and third-party data, claimed 500+ points -> Dynamic Arguments | evidence enrichment, tailored arguments, continuous A/B testing, end-to-end automation | mostly hands-free positioning, reporting and outcome learning | Dynamic evidence/argument generation is not whitespace. |
| **INDUSTRY CLAIM:** [Forter](https://docs.forter.com/product-overview) | processor/API/S3 chargebacks + merchant evidence -> stated AI optimization | eligibility recommendation, evidence request, package and automatic/manual/hybrid submission | portal metrics; issuer final decision | Public docs explicitly expose missing-evidence requests, narrowing our differentiation. |
| **INDUSTRY CLAIM:** [Signifyd](https://www.signifyd.com/emea/chargeback-recovery-for-merchants/) | order/fulfilment/chargeback + commerce-network history -> ML intent analysis | challenge abusive cases, honor legitimate ones, compile/file evidence | recovery insights and vendor win-rate claims | Network intent and automated recovery are mature. |
| **INDUSTRY CLAIM:** [Riskified](https://web-assets.riskified.com/pdfs/buyers-kit/Buyers-Kit_Riskified.pdf) | merchant/network transaction signals -> fraud decision models | approve/decline with chargeback guarantee in described offering | vendor assumes specified fraud liability | Checkout fraud and guarantees are not our problem. |
| **INDUSTRY CLAIM:** [Visa/Verifi](https://usa.visa.com/solutions/post-purchase-solutions/merchants.html) | network, issuer and merchant order data | Order Insight, RDR, CE3.0 and dispute optimization | issuer/network workflows; customizable resolution rules | Pre-dispute data sharing and CE automation are mature. |
| **INDUSTRY CLAIM:** [Mastercard Ethoca](https://newsroom.mastercard.com/news/media/etnfkpw2/building-digital-trust-by-combating-scams-and-fraudulent-merchants-may-2025.pdf) | issuer alerts and merchant data | alerts before escalation and dispute collaboration | merchant action on near-real-time alerts | Alerting is commoditized. |
| **INDUSTRY CLAIM:** [Adyen](https://docs.adyen.com/risk-management/understanding-disputes/dispute-reason-codes) | processor dispute events and reason-specific evidence | accept/defend via UI/API with network-specific documentation | merchant submits; issuer/network decide | Evidence rules and submission workflow are established. |
| **INDUSTRY CLAIM:** [PayPal](https://developer.paypal.com/platforms/disputes/integrate-disputes/) | dispute reason plus explicitly requested seller evidence | evidence API and repeated seller-response requests | PayPal adjudicates its workflow | Typed evidence requests are established. |
| **INDUSTRY CLAIM:** [Razorpay](https://razorpay.com/docs/payments/disputes/) | dispute/payment state, dashboard/API evidence | accept or contest; issuer reviews; some auto-refund behavior described | merchant responds, issuer decides | Our product must complement, not imitate, Razorpay's existing dispute surface. |
| **INDUSTRY CLAIM:** [Razorpay SHIELD](https://razorpay.com/blog/razorpay-upticks-success-rates-razorpay-shield) | Razorpay network and transaction signals -> AI/ML risk engine | international fraud risk and chargeback protection | vendor performance statements are not independently verified here | General transaction-risk scoring would collide with Razorpay's own stack. |

## Commoditized layers

- **RESEARCH RESULT:** Public product material establishes broad availability of dispute ingestion, evidence collection/enrichment, reason-aware packet construction, auto-submission, alerts, win prediction, A/B testing, network history and recovery reporting.
- **UNVERIFIED:** Public materials do not establish whether any provider lacks internal contradiction checking; absence from marketing is not proof of absence.

## Defensible whitespace test

- **HYPOTHESIS:** A pre-submission debugger that exposes exact learned claim spans, reconciles them with authoritative refund facts, fails safely under uncertainty, and shows a human repair decision diff reduces a measurable packet-integrity error not addressed explicitly in public product documentation.
- **DESIGN DECISION:** Differentiation is the testable interaction and assurance boundary, not exclusive ownership of evidence automation.
- **FAILURE CRITERION:** If domain-reviewed competitor trials or public documentation demonstrate equivalent exact-span contradiction debugging with repair recomputation and controlled abstention, the uniqueness claim is withdrawn and the product is positioned only as a Razorpay-specific implementation.

