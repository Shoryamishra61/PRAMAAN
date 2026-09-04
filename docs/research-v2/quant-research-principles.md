# Quant research principles

## Public evidence and bounded transfer

- **INDUSTRY CLAIM:** IMC publicly describes a workflow of hypotheses, historical back-tests, incremental changes against baselines, test series, and promotion only after acceptance. [IMC researcher interview](https://www.imc.com/ap/articles/this-world-has-changed-so-much-in-recent-years-meet-quant-researcher-liam)
- **INDUSTRY CLAIM:** Two Sigma publicly identifies repeatability as important for controlling and debugging ML experiments. [Two Sigma reproducibility article](https://www.twosigma.com/articles/a-workaround-for-non-determinism-in-tensorflow/)
- **INDUSTRY CLAIM:** Citadel Securities' public role description emphasizes rigorous research, back-testing, documentation and high-quality implementation; it is not public evidence of a particular fraud method. [Citadel Securities role](https://www.citadelsecurities.com/careers/details/machine-learning-researcher-phd-graduate-us/)
- **INDUSTRY CLAIM:** Jane Street publicly values research paired with usable software artifacts in an engineering context; this is a cultural signal, not a model-validation protocol. [Jane Street engineering note](https://blog.janestreet.com/jane-street-tech-talk-verifying-network-data-planes/)

## Applied rules for this project

1. **DESIGN DECISION:** Write the null, unit of deployment, metric and kill criterion before fitting a challenger.
2. **DESIGN DECISION:** The deployment unit is a complete evidence case; sentence-level extraction scores are necessary but insufficient.
3. **DESIGN DECISION:** Split by merchant/template/scenario/time before training; never let near-duplicate wording cross folds.
4. **DESIGN DECISION:** Preserve one untouched final holdout per benchmark version; all thresholding and calibration use TRAIN/DEV/calibration only.
5. **DESIGN DECISION:** Evaluate tail slices—amount qualifiers, temporal language, duplicate quotes, incomplete ledgers, prompt injection, malformed inputs and outages—rather than only mean F1.
6. **DESIGN DECISION:** Compare every added component with an ablation and the simplest viable baseline.
7. **DESIGN DECISION:** Measure stochastic variance, bootstrap paired deltas and threshold sensitivity; do not promote a single lucky seed.
8. **DESIGN DECISION:** Record data hash, code hash, model revision, environment, feature schema, seed, predictions and timing for every run.
9. **DESIGN DECISION:** Promotion is gated by financial safety and coverage, not by leaderboard rank alone.
10. **DESIGN DECISION:** Shadow, canary and rollback boundaries are defined before a model receives runtime traffic.

## Research anti-patterns

- **DESIGN DECISION:** No random split when an entity, time or template can leak.
- **DESIGN DECISION:** No tuning against the frozen v1 holdout.
- **DESIGN DECISION:** No synthetic benchmark metric presented as production impact.
- **DESIGN DECISION:** No SHAP/attention feature attribution described as causal explanation.
- **DESIGN DECISION:** No model is added because a prestigious firm or paper used the architecture elsewhere.

