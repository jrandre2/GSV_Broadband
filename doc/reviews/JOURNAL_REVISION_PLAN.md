# Journal Revision Plan: Conference to JIP Submission

> **Status:** In progress (pipeline complete; manuscript updated; JIP outputs rendered)
> **Created:** 2024-12-28
> **Target Journal:** Journal of Information Policy (JIP)

## Overview

**Title:** "What Predicts Broadband Usage? A Comparison of Computer Vision and Rural Urban Typology Machine Learning Models"

**Current Status:** Conference paper
**Target:** Journal of Information Policy
**Estimated additions:** ~2,800 words (total ~7,300, within JIP's 10,000 limit)

## Reviewer Checklist (next synthetic review)

- Manuscript: `manuscript_quarto/index.qmd` (methods/results reflect contiguity-based spatial CV and Appendix A).
- Canonical metrics: `data_work/diagnostics/estimation_results.csv` and `data_work/diagnostics/robustness_results.csv`.
- Spatial sensitivity: `data_work/diagnostics/spatial_sensitivity/spatial_sensitivity_summary.csv`.
- Cap sensitivity: `data_work/diagnostics/cap_sensitivity/max_images_*/estimation_results.csv` and `data_work/diagnostics/cap_sensitivity/max_images_*/robustness_results.csv`.
- Figures: `manuscript_quarto/figures/` (study area + spatial folds).
- Response log: `doc/reviews/PEER_REVIEW_RESPONSE_SR002.md` (status and resolved items).

---

## Peer Review Intake (SR-001)

See doc/reviews/PEER_REVIEW_SR001.md for the summary and doc/logs/peer_review_sr001.md for full text.
Status: Superseded by SR-002 (archived; not current).

## Peer Review Intake (SR-002)

See doc/reviews/PEER_REVIEW_SR002.md for the summary and doc/logs/peer_review_sr002.md for full text.
Status: Current.

Net-new items to incorporate in this plan:
- Clarify predictive (non-causal) framing and consider title refinement.
- Add a ZIP/ZCTA policy-use-case justification and aggregation caveats.
- Fully specify spatial CV protocol (fold definition, parameters, map).
- Add diagnostics for combined-model underperformance (block-level importance or stacking).
- Clarify RMSE/MAE units and add a short GSV terms-of-use/IRB statement.
- Consider a brief RUCA vs GSV policy cost comparison and optional out-of-region validation.

Net-new items to incorporate in this plan:
- Clarify construct validity (usage/adoption vs availability) and align framing.
- Add RUCA encoding baseline (one-hot + linear/ridge) and revisit the "non-linear" claim.
- Confirm PCA/scaling are fit within train folds; document leakage safeguards.
- Clarify sampling unit/counts (locations vs images per ZIP).
- Verify combined feature matrix includes RUCA; add stronger regularization/tuning.
- Increase metrics precision or resample reporting; sanity check distinct predictions.

---

## Peer Review Task Mapping (SR-001)

See doc/reviews/PEER_REVIEW_RESPONSE_SR001.md for validity assessment and point-by-point responses.

## Peer Review Task Mapping (SR-002)

See doc/reviews/PEER_REVIEW_RESPONSE_SR002.md for validity assessment and point-by-point responses.

### Additions from SR-002

- [x] Predict vs explain: add explicit non-causal framing.
- [x] Policy actionability: add a short ZIP/ZCTA use-case subsection and aggregation caveats.
- [x] Spatial CV protocol: specify fold construction and add a map/parameters.
- [x] Combined-model diagnostics: block-level importance or stacking baseline.
- [x] RMSE/MAE units: state scale and interpret as percentage points.
- [x] GSV ethics/terms: add terms-of-use and IRB/exemption statement.
- [ ] Policy cost comparison: RUCA vs GSV cost/time (optional).
- [ ] Out-of-region validation (optional).

### Pipeline + manuscript checklist (mapped to reviewer points)

- [x] Construct validity: align usage/adoption framing (no availability target added); report metrics from data_work/diagnostics.
- [x] RUCA encoding baseline: run s04_robustness RUCA encoding tests and add one-hot baseline to s03_estimation; update Table 1/figures from diagnostics.
- [x] Evaluation design: add repeated splits or K-fold CV and spatial CV; report mean +/- std from data_work/diagnostics/robustness_results.csv.
- [x] PCA leakage check: remove PCA from canonical pipeline; document fold-level preprocessing.
- [x] Image sampling clarity: reconcile total images vs modeling cap (s02_panel --max-images); report counts from linkage_summary.csv and panel_summary.csv.
- [x] Combined model fairness: verify RUCA concatenation, add tuning/regularization or residual modeling; document hyperparameters.
- [ ] Table precision: increase metric precision or report resample distributions; add sanity-check note.
- [ ] Data provenance + timeline + geography: add dataset citations, timeline table, and ZIP vs ZCTA clarification.
- [ ] Generalization evidence: add variance/cluster summaries or representative images; soften claims if not supported.
- [ ] Additional analyses: RUCA group-mean baseline and visual ablations completed; error analysis pending.
- [ ] Reproducibility: add selection rule and timeline table; feature specs, hyperparameter grids, and versions added.
- [x] Editorial: add limitations section and tighten terminology.

---

## Major Issues for Journal Publication

### 1. Missing Abstract

The manuscript has no abstract. For JIP and most journals, a 150-250 word abstract is essential.

**Action needed:** Resolved in front matter (abstract included in JIP render).

---

### 2. Insufficient Methodological Detail

**a) Feature Engineering Underspecified**

- Lists techniques (SIFT, ORB, AKAZE, BRISK, HOG, Haar Cascades, MobileNet) but doesn't specify:
  - Which features were actually retained in final models
  - How 24 features mentioned in Table 3 relate to the extensive list
  - Aggregation statistics beyond "mean and variance"
  - Dimensionality reduction if any

**b) Cross-Validation Unclear**

- "Group-based cross-validation strategy" mentioned but not fully specified
- Number of folds not stated
- How spatial groups were defined not explained
- Critical for reproducibility

**c) Hyperparameter Selection Missing**

- Tree depths, number of estimators not reported
- No discussion of hyperparameter tuning approach
- Regularization parameters not specified

**Action needed:** Add detailed methods subsection with specific parameters, feature counts, CV folds, and group definitions.

---

### 3. Literature Review Gaps for Journal Depth

**Missing connections:**

- No citation of foundational geospatial ML papers (Spatial autocorrelation literature)
- Limited engagement with why spatial CV matters (Brenning 2012, Roberts et al. 2017)
- No discussion of similar "null results" in transfer of urban CV methods to rural settings
- Multimodal fusion literature cited but not connected to implementation

**Action needed:** Expand lit review to ~2 additional pages connecting to spatial statistics and methodological transfer literature.

---

### 4. Results Presentation Needs Enhancement

**Current Issues:**

- Tables are informative but need clearer presentation
- No confidence intervals or significance tests
- Performance attribution (Table 3) methodology not explained
- No comparison to naive baselines (always predict mean)

**For journal standards:**

- Add uncertainty estimates to all performance metrics
- Explain how "Contribution" values in Table 3 were calculated
- Include baseline comparisons (mean predictor, random)
- Consider figures showing prediction residuals geographically

---

### 5. Discussion Lacks Theoretical Depth

**Strengths:**

- Visual homogeneity explanation is compelling
- Practical implications for future research clear

**Weaknesses:**

- No connection to spatial statistics theory (Tobler's First Law)
- Visual homogeneity argument is entirely post-hoc; could this have been anticipated?
- Limited engagement with why Nebraska specifically might show this pattern
- Satellite imagery suggestion needs more theoretical grounding

**Action needed:** Expand discussion to ~2 additional pages connecting findings to spatial theory and establishing a priori expectations.

---

### 6. Limitations Section Missing

Journal papers require explicit limitations. Current manuscript lacks:

- Sample size constraints (264 ZIPs, ~30 images/ZIP)
- Geographic scope (Nebraska only)
- Temporal alignment issues (imagery age vs. broadband data timing)
- Data source limitations (Microsoft telemetry may have biases)
- Model selection limitations (why these specific architectures?)

**Action needed:** Add dedicated Limitations subsection (400-500 words).

---

### 7. Reproducibility and Transparency

**Missing elements:**

- Data availability statement
- Code availability statement
- Supplementary materials reference
- Specific software versions

**Action needed:** Add Data Availability section per JIP requirements.

---

### 8. Figures Need Enhancement

Current figures (5 total) are functional but for journal:

- `fig_cv_comparison.png` - Needs clearer labeling
- `fig_feature_importance.png` - Should show confidence intervals
- `fig_spatial_groups.png` - Could show prediction residuals spatially

**Action needed:** Review and enhance figures with better legends, uncertainty visualization, and potentially additional diagnostic plots.

---

### 9. Writing and Structure Issues

**Structural:**

- Introduction is dense single paragraph; needs structuring
- Literature review section headers inconsistent
- "Exploring a New Method" section feels like conclusion to lit review rather than separate section

**Writing:**

- Some sentences overly long and complex
- Passive voice overused in methods
- Some claims lack hedging (e.g., "clear and compelling insight")

**Action needed:** Line editing pass; restructure introduction into 3-4 paragraphs.

---

### 10. Missing Elements for Journal Submission

Per JIP requirements:

- Alt text for figures (currently incomplete)
- Acknowledgments section
- Funding disclosure
- Conflict of interest statement
- Author contribution statement (if applicable)

---

## 10-Step Revision Plan

### Step 1: Add Abstract (New Section)

**Location:** After YAML front matter, before Introduction

**Content:**

- Research question: Can CV features supplement RUCA for broadband prediction?
- Study area: 264 Nebraska ZCTAs, 7,619 GSV images
- Methods: Ensemble models (Extra Trees, RF, GB) with spatial CV
- Key finding: RUCA + nonlinear models achieve R²=0.41; visual features contribute only 0.02
- Implication: Algorithm choice matters more than adding data modalities

**Length:** ~200 words

### Step 2: Restructure Introduction

**Current:** Single dense paragraph

**Revision:**

- Para 1: Policy urgency and funding landscape (existing content)
- Para 2: Gap statement - need for cost-effective methods
- Para 3: Research question and contribution preview
- Para 4: Paper organization

### Step 3: Expand Literature Review

**Add new subsection:** "Spatial Considerations in Machine Learning"

- Tobler's First Law and spatial autocorrelation
- Spatial CV importance (cite Roberts et al. 2017, Brenning 2012)
- Why random CV causes leakage in geographic data
- Transfer learning challenges in homogeneous landscapes

**Length:** ~600-800 words

### Step 4: Expand Methods Section

**Add to "Modeling and Evaluation":**

- Specify 5-fold spatial CV with geographic grouping
- Document all hyperparameters (n_estimators, max_depth, etc.)
- Explain how spatial groups were defined
- Add subsection on model comparison framework
- Include naive baseline (predict mean) for context

**Hyperparameters from `src/config.py:ML_MODELS`:**

- Extra Trees: n_estimators=100, max_depth=None, random_state=42
- Random Forest: n_estimators=100, max_depth=None, random_state=42
- Gradient Boosting: n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42

### Step 5: Add Uncertainty to Results Tables

- **Table 1:** Add confidence intervals or standard errors
- **Table 2:** Add CV standard deviations
- **Table 3:** Explain attribution methodology
- **Table 4:** Already has ± notation, verify against actual CV results
- **New Table:** Naive baseline comparison (mean predictor R²=0)

### Step 6: Deepen Discussion

**Add theoretical framework:**

- Connect visual homogeneity to Tobler's First Law
- Explain why Nebraska's landscape breaks urban CV assumptions
- Discuss spatial scale mismatch (ZIP vs. street-level)

**Add methodological contribution:**

- Importance of spatial CV in geographic ML
- When visual features transfer vs. fail
- Implications for other rural broadband studies

**Length:** ~600-800 additional words

### Step 7: Add Limitations Section

**New section after Discussion, before Conclusion**

**Content:**

1. Sample size: 264 ZIPs, ~30 images per ZIP
2. Geographic scope: Nebraska only; results may not generalize
3. Temporal alignment: GSV imagery age varies; broadband data timing
4. Data source bias: Microsoft telemetry may underrepresent some populations
5. Model selection: Other architectures not tested (CNNs directly on images limited by sample size)
6. Feature engineering: Many design choices not systematically ablated

**Length:** ~400-500 words

### Step 8: Add Required Front/Back Matter

**After references, add:**

- Data Availability Statement (code AND data will be publicly available)
- Code Availability Statement (GitHub repository link)
- Acknowledgments (if any)
- Funding Disclosure
- Conflict of Interest Statement

### Step 9: Complete Figure Alt Text

**File:** `manuscript_quarto/_output/jip_submission/alt_text.txt`

- Write descriptive alt text for all 5 figures
- Follow JIP accessibility guidelines

### Step 10: Editorial Polish

- Line edit for passive voice reduction
- Hedge strong claims ("clear and compelling" → "suggests")
- Check citation format (Chicago 18th ed, Notes-Bibliography)
- Verify all in-text citations appear in references.bib

---

## Priority Matrix

| Priority     | Issue                              | Effort |
| ------------ | ---------------------------------- | ------ |
| **Critical** | Missing abstract                   | Low    |
| **Critical** | Insufficient methodological detail | Medium |
| **Critical** | Missing limitations section        | Medium |
| **High**     | No uncertainty estimates           | Medium |
| **High**     | Discussion lacks theoretical depth | High   |
| **High**     | Data availability statement        | Low    |
| **Medium**   | Literature review expansion        | High   |
| **Medium**   | Figure enhancements                | Medium |
| **Low**      | Writing polish                     | Medium |

---

## Files to Modify

| File                                                | Changes                          |
| --------------------------------------------------- | -------------------------------- |
| `manuscript_quarto/index.qmd`                       | All content revisions            |
| `manuscript_quarto/figures/`                        | Enhanced figures with CIs        |
| `manuscript_quarto/_quarto.yml`                     | Any configuration updates        |
| `manuscript_quarto/_output/jip_submission/alt_text.txt` | Complete alt text            |

---

## Estimated Word Count

| Section           | Current | Addition    | New Total |
| ----------------- | ------- | ----------- | --------- |
| Abstract          | 0       | +200        | 200       |
| Introduction      | ~400    | restructure | ~400      |
| Literature Review | ~2000   | +700        | ~2700     |
| Methods           | ~800    | +400        | ~1200     |
| Results           | ~700    | +200        | ~900      |
| Discussion        | ~600    | +700        | ~1300     |
| Limitations       | 0       | +450        | 450       |
| Back matter       | 0       | +150        | 150       |
| **Total**         | ~4500   | +2800       | **~7300** |

*JIP limit: 10,000 words (excluding abstract/tables/refs) — well within range*

---

## Summary

The manuscript has a solid empirical foundation and an interesting finding (visual features don't help in visually homogeneous rural landscapes; RUCA + nonlinear models are sufficient). For journal publication, it needs:

1. **Structural completeness** - Abstract, limitations, data availability
2. **Methodological rigor** - CV details, hyperparameters, uncertainty quantification
3. **Theoretical depth** - Connect to spatial statistics, ground the visual homogeneity argument
4. **Journal compliance** - All required front matter, figure accessibility

The core contribution—demonstrating that algorithm choice matters more than adding data modalities, and that visual features don't transfer to homogeneous landscapes—is valuable and publishable with these enhancements.
