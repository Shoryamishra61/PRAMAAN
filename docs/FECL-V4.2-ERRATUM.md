# FECL-Bench v4.2 integrity erratum

Status: protocol correction before any v4 model fitting and before any v4 TEST access.

FECL-Bench v4.1 is preserved but invalid for model evaluation. A label-blind proof-compiler
audit found three benchmark defects:

1. `policy_exception` annotated a policy contradiction that was absent from the grounded claim.
2. `matching_amount_wrong_order` changed both order and payment identifiers, so it was not a
   single-cause minimal pair.
3. `promised_not_due_vs_overdue` changed both the promise deadline and authoritative refund
   status, so it was not a single-cause minimal pair.

v4.2 corrects these defects without changing the frozen split membership, family isolation,
counts, costs, or TEST-access protocol:

- every policy case grounds the explicit claim `This order is refund eligible`;
- every wrong-order case grounds the claimed order identifier and changes only that identifier;
- promise pairs use the same authoritative pending state and change only the grounded due date;
- temporal claims always expose their claimed completion date in the grounded span;
- proof compilation is forbidden from reading `phenomenon`, `ground_truth_label`,
  `material_contradiction`, `hard_constraints`, `required_for_resolution`, MCC annotations, or
  oracle trajectories.

The v4.2 generator must refuse overwrite, hash every split, and record that no v4-family model
was fitted and TEST was not evaluated before this correction.
