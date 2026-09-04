# Adjudication Protocol: Resolving Annotator Disagreements

**Standard:** Section 60–62 of Final Directive  

---

## 1. Committee Structure

Disputed cases are resolved by a panel consisting of:
- Lead FinTech Risk Scientist
- Domain Adjudicator (Senior Dispute Specialist)

---

## 2. Adjudication Rules

1. **Authoritative Ledger Supremacy:** If an annotator marked a case contradictory based on customer colloquialisms when the processor ledger definitively resolved the financial state, the processor ledger prevails.
2. **Ambiguity Default:** If genuine linguistic ambiguity exists (e.g., customer wrote "charged twice" referring to separate transactions on different dates without timestamps), the case ground truth is ruled `INCOMPLETE_EVIDENCE` requiring `REVIEW`.
3. **Audit Log:** Every adjudication decision must record:
   - `adjudicator_id`
   - `initial_disagreement_summary`
   - `resolution_rationale`
   - `timestamp`
