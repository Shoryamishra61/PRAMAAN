# FECL-Bench v4.1 erratum

Status: preregistered correction before any v4 model fitting or TEST evaluation  
Supersedes benchmark artifact: `artifacts/research/fecl-v4-benchmark-freeze.json`

The v4 benchmark passed structural leakage tests but failed a subsequent proof-compiler audit.
Five phenomena listed evidence that was not necessary for their compiled contradiction:

| Phenomenon | v4 over-complete list | v4.1 minimal list |
|---|---|---|
| matching amount, wrong order | order record + refund state | order record |
| overdue promise | policy + refund state | refund state |
| stale refund state | refund state + completion reference | refund state |
| source disagreement | confirmation + refund state | refund state |
| policy exception | policy + order record | policy |

`negation` also redundantly listed customer communication even though it is always initially visible;
v4.1 lists only the hidden refund state.

Because v4 labelled the supersets `minimal_relative_to_compiled_constraints`, its MCC exact-match and
active-acquisition-cost targets were invalid. No model had been fitted and TEST had not been parsed by
an evaluator. The v4 files and freeze remain immutable audit evidence. v4.1 regenerates every split
under a new dataset ID and new hashes; no v4 metric may be reported as v4.1.

All other `FECL-V4-PROTOCOL.md` hypotheses, counts, split families, model configurations, costs,
statistics and promotion gates remain unchanged.

