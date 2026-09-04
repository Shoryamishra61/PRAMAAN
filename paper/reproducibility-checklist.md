# Reproducibility checklist

- [x] Scientific question and promotion gates frozen before TEST.
- [x] Template-family-isolated train/DEV/TEST splits.
- [x] Minimal-pair counterfactual cases and explicit OOD set.
- [x] Deterministic seed `20260901`.
- [x] Pinned MiniLM model and revision.
- [x] Per-example raw and DEV-calibrated scores saved.
- [x] Confusion, PR-AUC, calibration, selective-risk and cost metrics saved.
- [x] Exact McNemar and 2,000-sample paired bootstrap reported.
- [x] Five MLP seeds reported separately.
- [x] Generated tables/plots derived from artifacts.
- [x] v1 frozen holdout not read by the v2 runner.
- [x] Runtime authority unchanged.
- [ ] Real merchant data validation (not available).
- [ ] Independent human annotation agreement (not available).
- [ ] External replication (not yet performed).

## Artifact hashes

- `FECL v2 DEV`: `3d891e7be669a5c9d40fc3c2fa0c63643cc0f3ed3f5caf945b1f157a3a9339c4`
- `FECL v2 freeze`: `4da3f9c5dd09c85cf64c0a39688bcdf771207cb4b1786aa61f4cda218a14aa4f`
- `FECL v2 TEST`: `053f53dd7a454625883f03387170b019c49454f355caa2222902662f4cb0f171`
- `FECL v2 post-hoc analysis`: `8a1b472e4f8b96777f3861297d3b38dc2d2078c067bef6b73a138903867a4a6c`
- `v1 frozen holdout`: `1508afc7a8bb8e9126970c7f1813eb0abf46213d77cfb270234eedb685423d28`
- `v1 grounding audit`: `ec549143fc4dc196dc16a2cebe06b3b518e9fe4ee261cf281cb3d269d1b25599`
