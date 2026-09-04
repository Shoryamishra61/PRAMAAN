# FECL-Bench v4.5 label-blind invariant-ontology erratum

Status: final benchmark candidate before model fitting and TEST access.

The v4.4 certificate audit found that `stale_refund_state` and `source_disagreement` encode the
same observable grounded proposition: a claimed refund status conflicts with authoritative refund
state. Assigning different invariant names requires reading the benchmark phenomenon label.

v4.5 maps both to `REFUND_STATUS`. The phenomenon field remains only a reporting slice and is
forbidden to the compiler and learned feature pipeline. This preserves every v4.4 correction and
changes no causal fact, split, family, cost, or TEST protocol. No model was fitted and TEST was not
evaluated before this correction.
