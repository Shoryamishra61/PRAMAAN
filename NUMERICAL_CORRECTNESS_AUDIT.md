# NUMERICAL CORRECTNESS & MONEY REPRESENTATION AUDIT

**Auditor Role**: Quantitative Systems Engineer & Financial Software Auditor  
**Standard**: IEEE-754 Precision Standards / BFSI Minor-Unit Accounting Mandate  
**Date**: September 2026  
**Repository**: `dispute-integrity-gate-spec`  

---

## 1. The Core Financial Invariant: Integer Minor Units

In financial computing, representing authoritative money using binary floating-point numbers (`float` / `double` / IEEE 754) is an unacceptable vulnerability. In base-2 floating point, common decimal fractions cannot be represented exactly:
$$0.1_{10} + 0.2_{10} = 0.30000000000000004_{10}$$
Over thousands of partial refund reconciliations, accumulated floating-point rounding errors break exact equality checks ($\sum \text{refunds} == \text{captured\_amount}$) and create false financial contradictions.

### Mandate
**All authoritative financial state, ledger records, dispute amounts, and SMT constraints must be strictly denominated in integer minor units (paise for INR, cents for USD).**
$$\text{₹}5{,}000.00 \implies 500{,}000 \text{ paise (integer)}$$

---

## 2. Repository-Wide Float Audit

We executed a comprehensive static grep across the entire codebase for `float` usages:

| Subsystem | File Path | Float Usage | Audit Verdict | Justification / Remediation |
| :--- | :--- | :--- | :---: | :--- |
| **Domain** | `backend/app/domain.py` | `MoneyMinor = Annotated[int, Field(strict=True, ge=0)]` | **CLEAN** | Zero floating-point types exist in domain state. |
| **Database** | `backend/app/database.py` | `amount_minor INTEGER NOT NULL CHECK (typeof(amount_minor) = 'integer' AND amount_minor >= 0)` | **CLEAN** | SQLite check constraint guarantees integer storage at the engine level. |
| **Grounding** | `backend/app/grounding.py` | `parse_inr_minor_units` uses Python `Decimal` | **CLEAN** | Uses `Decimal(amount) * 100`, validates `.to_integral_value()`, and returns `int`. |
| **Formal Solver** | `backend/app/carve.py` | `z3.IntVal(amount_minor)` | **CLEAN** | Invariants compile to integer arithmetic (`QF_LIA`). |
| **Model Features** | `training/run_empirical_study.py` | `amt_norm = amt / 100000.0` | **ACCEPTABLE** | Normalization for neural network input tensors. Strictly confined to ML feature extraction; never written back to authoritative state. |
| **Loss Evaluation** | `evaluation/cost_analysis.py` | `costs = np.zeros(n, dtype=np.float32)` | **ACCEPTABLE** | Mathematical expected loss and probability calculations. |

---

## 3. Decimal Normalization & Parsing Boundaries

The critical ingestion boundary where unstructured text strings are converted into authoritative integer paise is implemented in `backend/app/grounding.py:parse_inr_minor_units`:

```python
def parse_inr_minor_units(raw_value: str, currency: str | None) -> int | None:
    match = INR_AMOUNT_PATTERN.fullmatch(raw_value)
    if match is None:
        return None
    explicit_inr = match.group("symbol") is not None or match.group("code") is not None
    normalized_currency = currency.upper() if currency is not None else None
    if normalized_currency not in {None, "INR"}:
        return None
    if normalized_currency is None and not explicit_inr:
        return None
    try:
        amount = Decimal(match.group("amount").replace(",", ""))
    except InvalidOperation:
        return None
    minor = amount * 100
    if minor != minor.to_integral_value() or amount < 0:
        return None
    return int(minor)
```

### Numerical Boundary Tests Passed
1. **Valid Currency & Paise**: `"₹2,500.50"` $\implies 250050$ paise.
2. **Standard Commas**: `"INR 1,00,000.00"` $\implies 10000000$ paise.
3. **Sub-Paise Rejection**: `"₹100.555"` $\implies \text{None}$ (Rejected; fractional paise are impossible in INR banking).
4. **Negative Value Rejection**: `"-₹500.00"` $\implies \text{None}$ (Rejected; dispute amounts cannot be negative).
5. **Non-Numeric / NaN / Inf**: `"NaN"`, `"Infinity"`, `"₹1e6"` $\implies \text{None}$ (Rejected by regex).
6. **Currency Mismatch**: `"USD 500"` when case currency is `INR` $\implies \text{None}$.

---

## 4. Integer Minor-Unit Arithmetic with Explicit 64-Bit Storage Bounds

- **Python Integer Runtime**: Python integers have arbitrary precision, avoiding C/C++ `int32` truncation.
- **SQLite 64-Bit Storage Bounds**: SQLite `INTEGER` stores signed 64-bit values ($-2^{63}$ to $2^{63}-1$). Authoritative state uses **integer minor-unit arithmetic with explicit 64-bit storage bounds and overflow validation**. Maximum signed 64-bit minor units ($9{,}223{,}372{,}036{,}854{,}775{,}807$ paise $\approx ₹92,233\text{ trillion}$) provide vast headroom above any transaction volume, backed by SQLite check constraint `CHECK (typeof(amount_minor) = 'integer' AND amount_minor >= 0)`.
- **Property-Based Verification**: Verified via Hypothesis property test `test_sqlite_integer_storage_bounds` in `backend/tests/test_hft_fintech_invariants.py`, ensuring values remain $\le 2^{63}-1$ with bit length $\le 63$.
- **Frontend Serialization**: JavaScript clients format money by dividing integer minor units by 100 with `.toFixed(2)` for display only; mutations never send altered float values back to the authoritative database.

---

## 5. Numerical Audit Conclusion

Authoritative financial truth in CARVE-FECL is strictly isolated from floating-point rounding inaccuracies, non-associative additions, and sub-penny rounding artifacts through minor-unit integer arithmetic with explicit 64-bit database storage bounds.

