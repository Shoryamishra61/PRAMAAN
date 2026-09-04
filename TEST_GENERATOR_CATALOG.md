# PRAMAAN / CARVE-FECL — TEST GENERATOR CATALOG

> **Module**: `backend/tests/generators/strategies.py`  
> **Framework**: Hypothesis (Python)  
> **Philosophy**: Deliberately generate normal cases, boundary values, invalid values, extreme values, duplicates, and contradictions.

---

## 1. Generator Registry

### 1. `amounts_minor_strategy()`
- **Purpose**: Generates monetary amounts represented in integer minor units (paise/cents).
- **Partition Coverage**:
  - Boundary: `0`, `1`, `100`, `99999`, `500000`
  - Signed 64-bit limits: `2**63 - 1` ($9,223,372,036,854,775,807$)
  - Invalid types (fuzzing): negative integers, floating-point numbers, sub-paise values.
- **Hypothesis Definition**:
  ```python
  st.one_of(
      st.sampled_from([0, 1, 100, 99999, 500000, 2**63 - 1]),
      st.integers(min_value=0, max_value=10_000_000_00),
  )
  ```

---

### 2. `currencies_strategy()`
- **Purpose**: Generates currency identifiers across valid financial codes and corrupt inputs.
- **Partition Coverage**:
  - Valid supported: `"INR"`
  - Valid international: `"USD"`, `"EUR"`, `"GBP"`, `"SGD"`
  - Malformed / Invalid: lowercase (`"inr"`), numeric (`"356"`), symbols (`"₹"`), whitespace (`" INR"`).

---

### 3. `timestamps_utc_strategy()`
- **Purpose**: Generates timezone-aware UTC timestamps across realistic and edge temporal intervals.
- **Partition Coverage**:
  - Timestamps from year 2020 through 2030.
  - Microsecond boundary differences: $t$ vs $t + 1\mu\text{s}$.
  - Leap years, month boundaries, and daylight savings transitions.

---

### 4. `reference_ids_strategy()`
- **Purpose**: Synthesizes payment IDs (`pay_*`), refund IDs (`rfnd_*`), and Acquirer Reference Numbers (ARNs).
- **Partition Coverage**:
  - 12-digit UPI reference numbers.
  - 23-digit Visa/Mastercard ARNs.
  - Razorpay entity ID formats.
  - Boundary: empty string, whitespace padding, unicode characters.

---

### 5. `corrupted_text_strategy()`
- **Purpose**: Synthesizes real-world OCR and document scanning corruptions.
- **Partition Coverage**:
  - Digit confusion: `0` $\leftrightarrow$ `O`, `1` $\leftrightarrow$ `l` $\leftrightarrow$ `I`, `5` $\leftrightarrow$ `S`, `8` $\leftrightarrow$ `B`.
  - Whitespace mutations: stripped spaces, double tabs, newline insertions.
  - Unicode zero-width spaces (`\u200b`), smart quotes, and currency symbol variants.

---

### 6. `razorpay_webhook_payload_strategy()`
- **Purpose**: Synthesizes realistic and adversarial inbound webhook events.
- **Partition Coverage**:
  - Valid HMAC signature with unmodified payload.
  - Tampered body byte post-signing.
  - Extra whitespace or indentation in JSON body.
  - Rotated secret vs active secret.
  - Malformed JSON, non-JSON strings, and oversized payloads ($> 1\text{MB}$).

---

## 2. Replay & Reproduction Protocol

When a generated strategy triggers a property failure, Hypothesis outputs a reproduction block:

```python
@hypothesis.reproduce_failure("6.120.0", b"AXicY2BAAowMzEAMACQAAw==")
def test_failing_property():
    ...
```

Placing this decorator above the test replays the exact minimized failure case deterministically on any machine.
