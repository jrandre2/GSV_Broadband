# Peer Review Response (SR-001)

Status: Superseded by SR-002 (archived; not current).
Alias: SN-001.
Review date: 2025-12-28.
Source review: doc/logs/peer_review_sr001.md.
Assessment basis: manuscript_quarto/index.qmd, doc/METHODOLOGY.md, doc/PIPELINE.md, src/stages/s02_panel.py, src/stages/s03_estimation.py, data_work/diagnostics/conference/estimation_results.csv, data_work/diagnostics/robustness_results.csv.

Note: Pipeline outputs in data_work/diagnostics are canonical for reported metrics.

## Status Update (SR-001)

- Added RUCA one-hot baseline and tuned tree ensembles to holdout reporting (data_work/diagnostics/conference/estimation_results.csv).
- Added repeated CV, spatial CV, and nested tuning diagnostics including one-stage combined baselines (data_work/diagnostics/robustness_results.csv).
- Updated manuscript tables/text to separate baseline vs tuned holdout results and to reflect tuned spatial CV summaries (manuscript_quarto/index.qmd).
- Regenerated model comparison figures from current diagnostics (manuscript_quarto/figures).
- Completed copy-editing pass: tightened terminology, streamlined literature review, and added a Limitations section (manuscript_quarto/index.qmd).

## Strengths (acknowledged)

1) Clear comparative framing (RUCA vs visual vs combined)
- Validity: Accurate.
- Response: Acknowledge; retain framing.

2) Policy-relevant motivation
- Validity: Accurate.
- Response: Retain, but align framing to usage vs availability (see Major Issue 1).

3) Multiple model families compared
- Validity: Accurate.
- Response: Retain; add hyperparameter/tuning details.

4) High imagery coverage
- Validity: Accurate.
- Response: Retain; clarify how many images are used in modeling vs available.

## Major issues

1) Construct validity: usage vs availability/infrastructure
- Validity: Valid. Manuscript mixes infrastructure/availability language with a usage target.
- Evidence: manuscript_quarto/index.qmd:9, manuscript_quarto/index.qmd:41, manuscript_quarto/index.qmd:63.
- Response/action:
  - Manuscript: clarify adoption/usage target and limit infrastructure claims, or add an availability target as a robustness check.
  - Pipeline: if adding availability, update src/stages/s00_ingest.py and src/stages/s03_estimation.py; report metrics from data_work/diagnostics.

2) RUCA encoding and the "non-linear relationships" claim
- Validity: Valid for current holdout analysis; RUCA is treated as numeric in the conference reproduction code.
- Evidence: src/stages/s03_estimation.py:234, src/stages/s03_estimation.py:334.
- Response/action:
  - Add a one-hot RUCA baseline (linear/ridge) and compare to ensembles.
  - Use s04_robustness RUCA encoding results and update the manuscript language if categorical encoding narrows the gap.

3) Evaluation design (single split, no spatial CV)
- Validity: Valid; manuscript uses a fixed 80/20 split with seed 42.
- Evidence: manuscript_quarto/index.qmd:67.
- Response/action:
  - Report repeated splits or K-fold CV with mean +/- std.
  - Include spatial/grouped CV and report from data_work/diagnostics/robustness_results.csv (extend s04 if needed).

4) Potential leakage from PCA / feature pipeline order
- Validity: Needs verification. Manuscript references PCA; precomputed features include deep_pca columns, but PCA fit scope is not documented in the pipeline.
- Evidence: manuscript_quarto/index.qmd:59, data/processed/enhanced_all_features_20251228_124331.csv.
- Response/action:
  - Verify feature generation procedure and PCA fit scope.
  - If PCA was fit on full data, refit within train folds and update results; document safeguards in methods.

5) Image sampling intensity and unit clarity
- Validity: Valid; manuscript mixes total image counts with a 10-image-per-ZIP modeling cap.
- Evidence: manuscript_quarto/index.qmd:51, src/stages/s02_panel.py:134, doc/PIPELINE.md:41.
- Response/action:
  - Clarify sampling unit (location vs image), total available imagery, and subset used in modeling.
  - Use linkage and panel diagnostics to report counts (data_work/diagnostics/linkage_summary.csv, data_work/diagnostics/panel_summary.csv).

6) Fairness of RUCA vs visual comparison; combined underperforms
- Validity: Partially valid. Combined features do include RUCA, but underperformance suggests tuning/regularization issues.
- Evidence: src/stages/s03_estimation.py:334, data_work/diagnostics/conference/estimation_results.csv.
- Response/action:
  - Verify feature alignment and RUCA concatenation.
  - Add tuning or stronger regularization; consider residual modeling; document hyperparameters.

7) Table 1 identical metrics across models
- Validity: Valid; rounding to three decimals hides small differences.
- Evidence: manuscript_quarto/index.qmd:81, data_work/diagnostics/conference/estimation_results.csv.
- Response/action:
  - Increase precision or report distributions across resamples; add a brief sanity-check note.

## Secondary clarifications

A) Data provenance and citations
- Validity: Valid; manuscript lacks stable dataset citations for Microsoft usage, GSV APIs, and buildings footprints.
- Evidence: manuscript_quarto/index.qmd:51, manuscript_quarto/index.qmd:63.
- Response/action: Add dataset citations with versions and coverage.

B) Temporal alignment
- Validity: Valid; manuscript does not state the year(s) for usage data or imagery capture distribution.
- Evidence: manuscript_quarto/index.qmd:51.
- Response/action: Add a timeline table (RUCA year, imagery years, usage year).

C) Unit of geography: ZIP vs ZCTA
- Validity: Valid; terms are used interchangeably.
- Evidence: manuscript_quarto/index.qmd:45.
- Response/action: Clarify unit, geometry source, and linkage logic.

D) Generalization claims ("visually homogeneous")
- Validity: Valid; claim is not empirically demonstrated.
- Evidence: manuscript_quarto/index.qmd:116.
- Response/action: Add variance/cluster summaries or representative images, or soften the claim.

## Suggested analyses

1) Repeated evaluation + uncertainty
- Validity: Valid; not reported in manuscript.
- Response/action: Add repeated splits/K-fold and spatial CV; report mean +/- std from diagnostics.

2) RUCA encoding experiment
- Validity: Valid; results exist in robustness diagnostics but not reported.
- Evidence: data_work/diagnostics/robustness_results.csv.
- Response/action: Report categorical vs ordinal RUCA results and update narrative.

3) RUCA group mean baseline
- Validity: Valid; baseline not currently in pipeline.
- Response/action: Add a RUCA mean baseline in s04 or s03; report alongside models.

4) Incremental value conditional on RUCA
- Validity: Valid; not currently in pipeline.
- Response/action: Add residual modeling or within-RUCA evaluation to s04.

5) Visual feature ablation
- Validity: Partially addressed in pipeline plan but not reported in diagnostics.
- Response/action: Run ablations (OpenCV-only vs CNN-only vs combined) and report.

6) Error analysis
- Validity: Valid; not currently reported.
- Response/action: Add diagnostic listing highest-residual ZIPs and compare RUCA vs visual.

## Minor comments and editorial suggestions

1) Literature review vs methods length
- Validity: Subjective but likely; methods are brief relative to review.
- Response/action: Rebalance sections with more methodological transparency.

2) Terminology tightening
- Validity: Valid; "deep learning" vs "pretrained embeddings" and usage phrasing are inconsistent.
- Response/action: Standardize terminology across manuscript.

3) Limitations section
- Validity: Valid; missing in manuscript.
- Response/action: Add limitations covering telemetry bias, GSV coverage bias, spatial dependence, and generalization limits.

## Reproducibility checklist

- ZIP/ZCTA list and selection rule: Not documented; add selection rule and list or reference.
- Train/test split policy: Seed is stated, but stratification/spatial constraints are not; add details.
- Full feature specification: Add feature names, counts, and PCA components from diagnostics.
- Pipeline details: Add scaling/PCA fit scope and leakage safeguards.
- Hyperparameters/tuning: Document defaults or tuning method.
- Data availability statement: Add per journal requirements.

## Overall recommendation

- Recommendation: Major revision accepted; tracked in doc/reviews/JOURNAL_REVISION_PLAN.md.
