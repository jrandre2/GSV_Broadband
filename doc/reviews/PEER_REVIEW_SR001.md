# Peer Review Intake (SR-001)

Status: Superseded by SR-002 (archived; not current).
Alias: SN-001.
Review date: 2025-12-28.
Source: Synthetic peer review provided by user; manuscript dated 2025-12-28.
Full text: doc/logs/peer_review_sr001.md.

## Key strengths

- Clear comparative framing of RUCA vs street-level imagery.
- Policy-relevant motivation around cost-effective targeting.
- Multiple model families compared (linear, ElasticNet, tree ensembles).
- High GSV coverage across ZIPs for a rural setting.

## Major issues to address (priority)

- Construct validity: clarify whether the target is adoption/usage vs availability/infrastructure; align framing or add an availability proxy if feasible.
- RUCA encoding: state categorical handling; add one-hot RUCA + linear/ridge baseline; revisit the "non-linear relationships" claim.
- Evaluation design: replace single split with repeated splits or K-fold CV; add spatial/grouped CV; report mean +/- std.
- Pipeline hygiene: confirm scaling/PCA fit only on training folds; document leakage safeguards or rerun.
- Image sampling clarity: specify unit (location vs image), target per ZIP, and actual subset used in modeling; reconcile counts.
- Combined model fairness: verify RUCA concatenation; add regularization/tuning; explain why combined models underperform.
- Metrics table checks: add precision or resampling distributions; confirm distinct predictions across model classes.

## Secondary clarifications

- Data provenance: cite Microsoft usage dataset, GSV APIs, and buildings footprint dataset with versions.
- Temporal alignment: add a timeline table for RUCA year, imagery capture years, and usage year.
- Geography: clarify ZIP vs ZCTA usage and linkage.
- Generalization: support "visually homogeneous" claims with variance/cluster summaries or representative images.

## Suggested analyses (if time allows)

- RUCA group-mean baseline and residual modeling of visual features conditional on RUCA.
- Visual feature ablation (OpenCV-only vs CNN-only).
- Error analysis on highest-residual ZIPs.

## Integration notes

- Use `data_work/diagnostics` outputs for reported metrics; do not cite manuscript-only numbers.
- Track changes in `doc/reviews/JOURNAL_REVISION_PLAN.md`.
- Tuned holdout and spatial CV updates are logged in `data_work/diagnostics` and summarized in `doc/RESULTS_SUMMARY.md`.
