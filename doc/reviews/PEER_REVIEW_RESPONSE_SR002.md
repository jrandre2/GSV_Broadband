# Peer Review Response (SR-002)

Status: Current.
Review date: 2025-12-28.
Source review: doc/logs/peer_review_sr002.md.
Assessment basis: manuscript_quarto/index.qmd, doc/PIPELINE.md, src/stages/s02_panel.py, src/stages/s03_estimation.py, src/stages/s04_robustness.py, src/utils/feature_extraction.py, src/utils/spatial_cv.py, data_work/diagnostics/linkage_summary.csv, data_work/diagnostics/panel_summary.csv, data_work/diagnostics/pretrained_features/pretrained_features_20250728_233330.csv, data_work/diagnostics/cap_sensitivity/image_counts_summary.csv, data_work/diagnostics/cap_sensitivity/max_images_*/estimation_results.csv, data_work/diagnostics/cap_sensitivity/max_images_*/robustness_results.csv, data_work/diagnostics/conference/estimation_results.csv, data_work/diagnostics/robustness_results.csv, data_work/diagnostics/spatial_sensitivity/spatial_sensitivity_summary.csv.

Note: Pipeline outputs in data_work/diagnostics are canonical for reported metrics.

## Status Update (SR-002)

- Intake logged in doc/reviews/PEER_REVIEW_SR002.md and doc/logs/peer_review_sr002.md.
- Initial validity assessment and task mapping captured below; execution pending prioritization.
- Assessment rubric and execution plan added; P0 tasks queued.
- Stage 03 spatial CV scaling fix applied; cap-sensitivity diagnostics saved; feature pipeline audit completed.
- Cap-sensitivity rerun on the enhanced_processed corpus; diagnostics refreshed.
- Stage 02 now retains all 24 OpenCV features; robustness expanded (RUCA group-mean, RUCA2, late-fusion, block diagnostics); figures regenerated; manuscript methods/results updated.
- Spatial CV now uses contiguity-based folds; spatial grouping sensitivity diagnostics added.
- Copy-edit pass completed; Appendix A added for spatial CV sensitivity; Quarto outputs rendered (default and JIP profiles).

## Assessment Rubric (SR-002)

- Accuracy: Confirmed / Partial / Unclear / Not supported.
- Value: High / Medium / Low (impact on validity, generalization, policy use, reproducibility).
- Priority: P0 (must fix), P1 (important), P2 (nice-to-have).
- Action: Manuscript / Analysis / Audit / Both.

## Critique Assessment Matrix (SR-002)

- SR002-1 Predict vs explain | Accuracy: Partial | Value: High | Priority: P0 | Evidence: manuscript_quarto/index.qmd | Action: Manuscript
- SR002-2 ZIP/ZCTA policy use | Accuracy: Valid | Value: High | Priority: P0 | Evidence: manuscript_quarto/index.qmd | Action: Manuscript
- SR002-3 Sampling + 10-image cap | Accuracy: Valid | Value: High | Priority: P0 | Evidence: data_work/diagnostics/cap_sensitivity/image_counts_summary.csv, data_work/diagnostics/panel_summary.csv, src/stages/s02_panel.py | Action: Analysis + Manuscript
- SR002-4 Leakage (PCA/scaling) | Accuracy: Partial | Value: High | Priority: P0 | Evidence: manuscript_quarto/index.qmd, src/stages/s03_estimation.py, data_work/diagnostics/cap_sensitivity/max_images_*/estimation_results.csv | Action: Fix + Manuscript
- SR002-5 Spatial CV specification | Accuracy: Valid | Value: High | Priority: P0 | Evidence: src/stages/s02_panel.py, src/utils/spatial_cv.py, src/stages/s04_robustness.py | Action: Manuscript + Figure
- SR002-6 Combined model underperformance | Accuracy: Valid | Value: Medium | Priority: P1 | Evidence: data_work/diagnostics/conference/estimation_results.csv | Action: Analysis
- SR002-7 RUCA baseline contextualization | Accuracy: Valid | Value: Medium | Priority: P1 | Evidence: data_work/diagnostics/robustness_results.csv | Action: Analysis + Figure
- SR002-8 Target validity and policy framing | Accuracy: Valid | Value: Medium | Priority: P1 | Evidence: manuscript_quarto/index.qmd | Action: Manuscript
- SR002-9 Reproducibility details | Accuracy: Valid | Value: Medium | Priority: P1 | Evidence: doc/PIPELINE.md, src/config.py, data_work/diagnostics | Action: Manuscript + Appendix
- SR002-10 Feature pipeline mismatch (CNN/PCA claim vs CV features used) | Accuracy: Confirmed | Value: High | Priority: P0 | Evidence: src/stages/s02_panel.py, src/utils/feature_extraction.py, data_work/diagnostics/pretrained_features/pretrained_features_20250728_233330.csv, data_work/panel.parquet schema | Action: Audit + Manuscript

## Execution Plan (SR-002)

P0 (accuracy + validity)
- Reconcile feature pipeline vs manuscript (OpenCV-only vs pretrained features; CNN/PCA claim); update manuscript or pipeline to match canonical diagnostics.
- Fix scaling leakage in spatial CV for Stage 03 (fit scaler within folds via Pipeline); re-run diagnostics for affected CV metrics.
- Sampling/cap sensitivity: build panels with --max-images 5/10/20/all; re-run estimation + robustness; log outputs in data_work/diagnostics.
- Spatial CV specification: document contiguity-based grouping and parameters (queen/rook, n_groups); produce fold map via s05_figures; run grouping sensitivity.

P1 (interpretability + positioning)
- Combined-model diagnostics (block-level importance; confirm RUCA categorical handling; consider late-fusion baseline).
- RUCA group-mean baseline + usage-by-RUCA distribution and residual map.
- Expand target validity and policy use case; add reproducibility appendix (features, grids, versions, availability).

P2 (optional)
- Out-of-region validation, policy cost comparison, OpenCV vs CNN ablations (if CNN features remain in scope).

## Pipeline Audit Findings (Feature + Imagery Alignment)

- Stage 02 now retains all 24 OpenCV features in the canonical panel; Stage 03/04 use the full 24-feature set after the selection fix.
- The conference precomputed features include deep_pca columns; the canonical pipeline does not use CNN/PCA features.
- Image inventory (enhanced_processed corpus): 7,619 images across 261 ZIPs (mean 29.2). Cap sensitivity (5/10/20/all) yields combined spatial CV -0.050 to -0.019 and visual-only -0.196 to -0.173; conclusions unchanged.
- Panel schema confirms all 24 OpenCV features are present in the canonical panel.

## Manuscript Alignment Edits (Implemented)

- Updated GSV sampling description to reflect current image inventory and non-binding cap.
- Replaced CNN/PCA feature description with the OpenCV feature set used in the canonical pipeline.
- Clarified that the default pipeline uses 24 OpenCV features (no CNN/PCA).
- Updated model descriptions, spatial CV protocol, and diagnostics references to canonical outputs.

## Status (Current)

- P0 items completed: feature pipeline aligned; scaling leakage fixed; cap sensitivity documented; spatial CV map generated and cited; contiguity-based folds and grouping sensitivity added.
- P1 items completed: RUCA group-mean baseline, RUCA2 checks, late-fusion, block diagnostics, RUCA distribution + residual map figures, policy framing, target validity, reproducibility section.
- Remaining: optional analyses only (out-of-region validation, policy cost comparison, CNN ablations).

## Strengths (acknowledged)

1) Policy-relevant framing and negative-result message
- Validity: Accurate.
- Response: Retain; keep policy relevance explicit.

2) Clear RUCA vs visual vs combined comparisons
- Validity: Accurate.
- Response: Retain; keep tables separated (baseline vs tuned).

3) Inclusion of spatial validation
- Validity: Accurate; spatial CV results are reported from diagnostics.
- Response: Retain and expand protocol detail.

4) Clear reporting of key metrics
- Validity: Accurate; metrics are in current tables.
- Response: Retain; ensure units are stated.

## Major issues

1) Clarify inferential claim: "predicts" vs "explains"
- Validity: Partially valid. The manuscript is predictive but could better disavow causal interpretation.
- Evidence: manuscript_quarto/index.qmd (title, Introduction, Discussion).
- Response/action: Add explicit non-causal statement; adjust wording to "predict/forecast" where needed; consider title refinement.

2) ZIP/ZCTA unit and policy actionability
- Validity: Valid. Current text does not justify ZIP-level targeting use cases.
- Evidence: manuscript_quarto/index.qmd (Data and Methods).
- Response/action: Add a short "Policy use case" subsection and discuss aggregation limits.

3) Street View sampling methodology and cap
- Validity: Valid. The description mixes a 500-structure manifest, total images, and a 10-image cap.
- Evidence: manuscript_quarto/index.qmd; src/stages/s02_panel.py; data_work/diagnostics/cap_sensitivity/image_counts_summary.csv.
- Response/action: Cap sensitivity completed (data_work/diagnostics/cap_sensitivity). Image inventory is 7,619 images across 261 ZCTAs; cap sensitivity results reflect 5/10/20/all caps; reconcile manuscript sampling text as needed.

4) Preprocessing leakage (PCA/scaling)
- Validity: Partially valid. Scaling is now fit within folds; PCA is still claimed in the manuscript but not present in the canonical pipeline.
- Evidence: manuscript_quarto/index.qmd; src/stages/s03_estimation.py; data_work/diagnostics/cap_sensitivity/max_images_*/estimation_results.csv.
- Response/action: Keep fold-level scaling; update manuscript to remove PCA claims or implement PCA within-fold if embeddings are reintroduced; document pipeline order.

5) Spatial cross-validation specification
- Validity: Valid. Spatial CV is reported but not fully specified in the manuscript.
- Evidence: manuscript_quarto/index.qmd; src/stages/s04_robustness.py.
- Response/action: Add protocol subsection with contiguity-based fold construction, parameters, and map; report distribution (not only mean +/- SD); add grouping sensitivity results.

6) Combined model underperformance diagnostics
- Validity: Valid. Diagnostics show combined models below RUCA-only on holdout.
- Evidence: data_work/diagnostics/conference/estimation_results.csv.
- Response/action: Ensure categorical RUCA in combined pipelines; add block-level diagnostics (coeff norms or permutation importance); evaluate stacked/late-fusion baseline.

7) RUCA baseline contextualization
- Validity: Valid. RUCA performance could reflect category means.
- Evidence: data_work/diagnostics; manuscript lacks a RUCA group-mean baseline.
- Response/action: Add RUCA group-mean baseline; add usage-by-RUCA distributions and residual map.

8) Target validity and policy interpretation
- Validity: Valid. Usage/adoption implications need expansion.
- Evidence: manuscript_quarto/index.qmd.
- Response/action: Add data-year/coverage details; highlight adoption vs availability implications and biases.

9) Reproducibility expectations
- Validity: Valid. Feature list, PCA components, and hyperparameters are incomplete.
- Evidence: manuscript_quarto/index.qmd; doc/PIPELINE.md.
- Response/action: Add reproducibility appendix (feature list, PCA components, hyperparameter grids, software versions) and a data availability statement.

## Suggested analyses (optional)

- Sensitivity to image count caps and equal-weight aggregation by ZIP.
- Policy cost comparison (RUCA vs GSV pipeline costs).
- Out-of-region validation.
- Feature-block ablations (OpenCV vs CNN vs both).

## Minor comments and editorial fixes

- ZIP vs ZCTA terminology: Valid; standardize and clarify early.
- RMSE/MAE units: Valid; state whether target is in [0,1] or [0,100] and interpret as percentage points.
- RUCA numeric baseline: Valid; label as naive numeric encoding or drop.
- LiDAR footnote formatting: Valid; fix numbering/text.
- Reference hyphenation artifacts: Valid; clean references.
- RUCA2 omission: Valid; add brief test result or rationale.
- GSV ethics/terms: Valid; add a short terms-of-use/IRB statement.
