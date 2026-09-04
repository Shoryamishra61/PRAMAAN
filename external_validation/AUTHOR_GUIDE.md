# Author Guidelines: External Independent Blind Challenge Pack

**Standard:** Section 26 of Final Directive  
**Status:** Protocol Frozen / Pending Execution  

---

## 1. Objective for Case Authors

Your goal as an independent author is to write realistic dispute correspondence and merchant evidence packets based on a **structured scenario brief**.

You must NOT:
- View any system generator templates or benchmark source code.
- View CARVE-FECL model predictions or rule definitions.
- View the adjudication outputs of previous cases.
- Alter or revise any text once model inference has run on your batch.

---

## 2. Inputs Provided to Authors

Each author receives 100 scenario briefs formatted as:
```json
{
  "scenario_id": "SCEN_1042",
  "category": "CREDIT_NOT_PROCESSED",
  "latent_state": {
    "purchase_amount_inr": 4999.00,
    "authorized_amount_inr": 4999.00,
    "captured_amount_inr": 4999.00,
    "refund_initiated": true,
    "refund_settled": false,
    "settled_amount_inr": 0.00,
    "delivery_status": "DELIVERED"
  },
  "required_documents": ["CUSTOMER_CHAT", "MERCHANT_NOTE", "PROCESSOR_LEDGER"]
}
```

---

## 3. Authoring Instructions

1. **Write Natural Human Text:** Write the customer's complaint in realistic language (colloquial English, Indian English, or formal tone). Include realistic nuances such as frustration, timestamps, order IDs, and payment references.
2. **Honor the Latent State:** If the latent state specifies `refund_settled = false`, ensure the authoritative ledger reflects `PENDING` or `FAILED`. The customer may either mistakenly claim it was settled (creating a material contradiction) or accurately state it is missing (creating an evidence sufficiency hold).
3. **No Synthetic Shortcuts:** Avoid using formulaic sentences such as `"The refund of ₹4,999 was processed on 05 May."` Instead write natural prose: `"Hey, I checked my bank statement today and the 5k refund still hasn't reflected after 10 days, what is going on?"`
