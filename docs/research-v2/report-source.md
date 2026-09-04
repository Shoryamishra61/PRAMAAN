# Research-v2 canonical report source

**Date:** 2026-09-01  
**Scope:** Razorpay Track 02, refund/credit-not-processed evidence integrity  
**Status:** Research and design specification; no new model is promoted.

## Executive conclusion

- **RESEARCH RESULT:** The global review falsifies broad novelty claims around AI evidence generation, automated representment, win prediction, graph fraud and formal risk control.
- **DESIGN DECISION:** The smallest defensible product is a financial evidence debugger: grounded claim -> deterministic refund reconciliation -> visible contradiction -> safe decision -> human repair -> live diff.
- **RESEARCH RESULT:** Frozen v1 results justify the problem but reject every learned runtime challenger; the rules extractor remains active.
- **DESIGN DECISION:** The new contribution is a falsifiable research program for exact-span material claims and cross-source relations under explicit selective risk, not a larger stack.

## Artifact map

1. [Problem decomposition](problem-decomposition.md)
2. [Global literature review](global-literature-review.md)
3. [Asian fintech review](asian-fintech-research-review.md)
4. [Quant research principles](quant-research-principles.md)
5. [Competitor forensics](competitor-forensics.md)
6. [Patent landscape](patent-landscape.md)
7. [Research hypotheses](research-hypotheses.md)
8. [Model tournament](model-tournament.md)
9. [Evidence graph study](evidence-graph-study.md)
10. [Risk-control study](risk-control-study.md)
11. [Dataset and labeling plan](dataset-and-labeling-plan.md)
12. [Evaluation protocol](evaluation-protocol.md)
13. [High-level system design](high-level-system-design.md)
14. [ML system architecture](ml-system-architecture.md)
15. [Interactive product spec](interactive-product-spec.md)
16. [Novelty falsification](novelty-falsification.md)
17. [Final go/no-go](final-go-no-go.md)

## Claim-to-source index

- **FACT:** Razorpay scope/evidence: [Track site](https://razorpay.com/buildathon/), [disputes](https://razorpay.com/docs/payments/disputes/), [submit evidence](https://razorpay.com/docs/payments/disputes/submit-evidence/).
- **INDUSTRY CLAIM:** Competitors/networks: [Stripe](https://docs.stripe.com/disputes/smart-disputes), [Chargeflow](https://docs.chargeflow.io/docs/reference/concepts/dispute-automation), [Justt](https://justt.ai/platform/), [Forter](https://docs.forter.com/product-overview), [Signifyd](https://www.signifyd.com/emea/chargeback-recovery-for-merchants/), [Visa](https://usa.visa.com/solutions/post-purchase-solutions/merchants.html), [PayPal](https://developer.paypal.com/platforms/disputes/integrate-disputes/).
- **RESEARCH RESULT:** Grounding/relations: [ContractNLI](https://aclanthology.org/2021.findings-emnlp.164/), [Fast Evidence Extraction](https://aclanthology.org/2024.fever-1.24/), [FactRel](https://aclanthology.org/2024.starsem-1.15/).
- **RESEARCH RESULT:** Graph/fintech: [CARE-GNN](https://arxiv.org/abs/2008.08692), [PC-GNN](https://doi.org/10.1145/3442381.3449989), [xFraud](https://www.vldb.org/pvldb/vol15/p427-rao.pdf), [Ant Pareto rules](https://arxiv.org/abs/2311.00964), [SEFraud](https://arxiv.org/abs/2406.11389).
- **RESEARCH RESULT:** Risk: [Calibration](https://proceedings.mlr.press/v70/guo17a.html), [SelectiveNet](https://proceedings.mlr.press/v97/geifman19a), [CRC](https://proceedings.iclr.cc/paper_files/paper/2024/file/f3549ef9b5ff520a7e41ff3cc306ab2b-Paper-Conference.pdf), [Energy OOD](https://proceedings.neurips.cc/paper/2020/hash/f5496252609c43eb8a3d147ab9b9c006-Abstract.html), [DISCO](https://doi.org/10.1016/j.dss.2026.114717).
- **FACT:** Prior art: [PayPal 2025](https://patents.google.com/patent/US20250200587A1/en), [Bolt](https://patents.google.com/patent/US20210390550A1/en), [PayPal 2021](https://patents.google.com/patent/US11049112B2/en), [Worldpay](https://patents.google.com/patent/EP4473465A1/en).

## Evidence boundary

- **FACT:** All new external metrics remain source-reported and are not product results.
- **FACT:** All product model metrics remain those in saved local v1 artifacts.
- **UNVERIFIED:** No real merchant case set, production outcome validation or measured loss reduction exists yet.

