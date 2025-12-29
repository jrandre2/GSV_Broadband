# Peer Review (SR-003)

Review date: 2025-12-28.
Source: synthetic peer review provided by user.
Journal: Journal of Information Policy

## Overall Assessment and Recommendation

This preprint asks a well-scoped, policy-relevant measurement question: does Google Street View-derived visual information add predictive value for broadband usage beyond a low-cost rural-urban typology? The paper is commendably transparent about negative/limited findings and, importantly, demonstrates how spatially aware validation can dramatically reduce apparent performance, which is a valuable methodological contribution for information policy scholarship that increasingly encounters "AI for policy" claims.

That said, as a submission to the Journal of Information Policy, the manuscript would benefit from major revisions before it is ready for publication. The biggest issues are (i) clarity and consistency in the spatial validation narrative (the abstract vs. the "canonical" spatial CV results), (ii) insufficient detail on the imagery sampling/linkage procedure, and (iii) insufficient policy framing of what the models would be used for, what error types matter, and how the data sources' biases could shape decisions.

**Recommendation: Major revision (revise-and-resubmit).**

## 1. Summary of What the Paper Does

The study predicts ZCTA-level broadband usage (interpreted as the estimated share using internet at or above 25/3 Mbps) across 264 ZCTAs in Nebraska, using (a) RUCA (RUCA1) as a rural-urban typology and (b) handcrafted OpenCV features extracted from Google Street View (GSV) images.

Imagery coverage is reported for 261/264 ZCTAs, totaling 7,619 images; features are averaged to the ZCTA level (with an extraction cap of 10 images/ZCTA in the main setup).

Models include linear/ElasticNet and tree ensembles (RF, ExtraTrees, GBRT) under three feature sets: RUCA-only, visual-only, and combined. Performance is assessed via a fixed 80/20 holdout split and via spatial cross-validation using contiguity-based grouped folds (queen contiguity clustering).

Key results: on the random holdout, tuned RUCA-only approaches reach test R^2 = 0.40, visual-only = 0.37, and combined models do not exceed RUCA-only. Spatial CV yields much weaker (often negative) R^2 values, suggesting limited geographic generalization.

## 2. Fit to Journal of Information Policy

The topic is clearly within JIP's remit: broadband policy, digital divide measurement, and the governance consequences of measurement choices.

However, the current presentation is closer to a methods paper in applied ML/geospatial analytics than a JIP paper unless you strengthen:
- the policy use case (who uses this, when, to decide what?),
- the measurement politics (what it means to rely on Microsoft telemetry and proprietary imagery),
- the normative implications (equity, transparency, accountability, reproducibility constraints).

The paper already gestures toward a screening/triage use case and cautions against fine-grained targeting, which is good. But JIP readers will likely expect a deeper policy argument than "typology is cheap and works well here."

## 3. Major Strengths

**Clear comparative design and negative result value.** You explicitly compare RUCA-only, visual-only, and combined models and report that imagery doesn't improve on RUCA in this setting. Negative results are important in a literature prone to "AI optimism."

**Inclusion of spatial validation.** The sharp drop from random holdout to contiguity-based spatial CV is a crucial and policy-relevant message: models that look useful under naive evaluation may not generalize geographically.

**Transparency about limitations.** You acknowledge sample size/region limits, temporal misalignment (RUCA 2010 vs imagery dates vs telemetry), and that handcrafted features limit conclusions about "imagery" more broadly.

**Reproducibility details are unusually explicit for a preprint.** The paper lists hyperparameter grids and software versions, which is helpful.

## 4. Major Concerns and Required Revisions

### 4.1 Clarify the Study Area: The Figures Suggest This Is Not "All of Nebraska"

The manuscript repeatedly frames the sample as "Nebraska," but Figure 1 and Figure 2 visually show a highlighted subset concentrated in the eastern portion of the state, not the full state polygon.

This matters because:
- It affects the paper's generalizability claims ("Nebraska" vs "eastern Nebraska corridor").
- It affects interpretation of "visual homogeneity": the included region may be less heterogeneous than Nebraska overall.
- It affects spatial CV: folds appear to be built over this restricted corridor, which may change the nature of geographic separation.

**Actionable fix:**
Add a subsection that answers:
- What exactly defines the "study area" (why those 264 ZCTAs and not others)?
- Are excluded ZCTAs missing Microsoft labels, RUCA codes, imagery, shapefiles, or something else?
- Provide a simple table summarizing included vs excluded units (counts + reasons).

### 4.2 The "Spatial CV" Story Is Internally Inconsistent Across Sections

There are several places where the spatial-validation story is hard to reconcile:
- The abstract says spatial CV yields "best RUCA around 0.13; visual and combined near zero or negative."
- Yet the main results emphasize contiguity-based spatial CV as "canonical," and report RUCA categorical ridge -0.276 +/- 0.186, RUCA group-mean baseline -0.309 +/- 0.208, tuned RF -0.209 +/- 0.136 (all negative).
- Appendix Table A1 shows that alternative spatial splits can produce positive mean R^2 (e.g., longitude bands 0.219 +/- 0.164; latitude bands 0.120 +/- 0.206; spatial blocks 0.113 +/- 0.262).

So the paper currently mixes:
- "canonical contiguity CV results are negative," and
- "best spatial CV is ~0.13," and
- "sensitivity can reach ~0.22,"
without a crisp hierarchy of what readers should believe and why.

**Actionable fix:** Choose and clearly communicate one of these narratives:
- **Narrative A (most conservative):** "Under contiguity-based spatial CV (our preferred deployment-relevant scheme), generalization is poor/negative across all models; other split definitions yield somewhat higher R^2 but are less conservative."
- **Narrative B (deployment-specific):** "If the deployment is to predict within the corridor with similar north/south structure, then longitude-band splits may reflect plausible extrapolation; contiguity splits may be overly strict for the intended use."

Either is defensible, but the abstract and discussion must match the "canonical" choice.

### 4.3 Spatial CV Methodology Needs More Precision (Fold Construction, Balance, and "Repeats")

You state you "construct five contiguous geographic folds by clustering adjacent ZCTA polygons using queen contiguity ... and evaluate with GroupKFold," and also refer to "repeated CV uses 5 splits x 10 repeats."

But GroupKFold is not inherently repeatable unless you (a) regenerate groups multiple times, or (b) vary the grouping algorithm seed, or (c) use repeated blocked subsampling. This is not explained.

Also, the appendix shows queen and rook contiguity results are identical across models and metrics. That might be possible in rare cases, but it's more often a sign that (i) the same groups were reused, (ii) rook/queen adjacency ended up identical due to preprocessing, or (iii) copy/paste. This needs to be clarified.

**Actionable fix:** Include:
- The exact algorithm used to create the 5 contiguous groups (e.g., SKATER, region-growing, agglomeration constrained by adjacency, etc.).
- Fold sizes (n per fold) and basic label distribution per fold.
- Whether "10 repeats" means 10 independent group constructions; if so, report variability due to grouping.
- A short justification of why 5 groups (vs 10, leave-one-county-out, buffered spatial blocking, etc.) is appropriate for n=264.

### 4.4 Imagery Sampling and Linkage Procedure Is Underspecified

Section 3.1.1 says GSV imagery is linked to ZCTAs using "a linkage procedure," but the manuscript does not provide enough detail for readers to evaluate bias or reproducibility.

**Critical details missing or too vague:**
- How were points sampled within each ZCTA (random road points, population-weighted, address-based, grid, centroids + jitter, etc.)?
- Were images taken in one heading or multiple headings?
- What were the API parameters: FOV, pitch, image size, date constraints (if any)?
- Were image timestamps/metadata stored, and did you filter by capture year?
- If you capped at 10 images/ZCTA, how were the 10 chosen (random subset vs first 10 returned vs fixed order)? Non-random selection could bias the aggregated features.

**Actionable fix:** Provide a reproducible protocol description and, ideally, a small schematic. If you cannot share raw imagery, you can still share:
- the sampling points (lat/longs),
- the API request parameters,
- and a hash list of URLs/metadata.

### 4.5 The Combined-Model Results Raise a Possible Implementation/Encoding Concern

In Table 1, "Visual only ElasticNet" and "Combined ElasticNet" have exactly the same test metrics (R^2=0.299, RMSE=0.244, MAE=0.194).

That could happen by coincidence, but exact equality across all three metrics strongly suggests either:
- RUCA was not actually included in the "combined ElasticNet" pipeline,
- RUCA was included but encoded in a way that contributed nothing (e.g., constant, or removed),
- or there is a reporting/copy error.

Additionally, the RUCA-only performance is highly sensitive to encoding (numeric RUCA baseline R^2=0.144 vs one-hot ridge R^2=0.400). That makes RUCA encoding a central methodological issue. If the combined models used numeric RUCA while RUCA-only used one-hot, the "combined underperforms RUCA-only" conclusion may partly be an artifact of inconsistent encoding.

**Actionable fix:**
- Explicitly state how RUCA is encoded in each model class (numeric vs one-hot) and keep encoding consistent across RUCA-only and combined comparisons.
- Double-check and report a diagnostic: does the combined ElasticNet actually assign nonzero coefficients to RUCA features?
- If the combined models truly perform worse than RUCA-only under the same encoding, explain why (overfitting due to added noise features; small sample; regularization mis-tuning).

### 4.6 Clarify the Construct Validity of the "Broadband Usage" Target and Its Policy Interpretation

You use Microsoft Research's "U.S. Broadband Usage Percentages" dataset and interpret it as "usage/adoption proxy," noting potential underrepresentation and that the file lacks an explicit year.

This is important, but for JIP the manuscript should go further:
- What is the normative risk of treating telemetry-based "usage at 25/3" as ground truth?
- Could it systematically undercount certain groups (low-device households, non-Microsoft ecosystems, mobile-only users)?
- If the target itself is biased, then a model that predicts it well may replicate the bias-this is directly a policy governance issue.

**Actionable fix:** Add a short "measurement governance" subsection:
- Why this dataset is chosen over ACS adoption measures or speed-test datasets,
- what forms of bias likely exist,
- and what safeguards should be used if such predictions inform funding, outreach, or enforcement.

### 4.7 The Policy Use Case Needs Sharper Articulation and Policy-Relevant Evaluation Metrics

You position the ZCTA-level approach as a "screening or triage tool" rather than fine-grained targeting.

That's a reasonable policy niche. But the evaluation remains almost entirely in terms of R^2/RMSE/MAE.

Policy users often care about:
- identifying bottom decile/quintile areas,
- minimizing false negatives (missing truly underserved communities),
- robustness across geography,
- and interpretability/traceability.

**Actionable fix:** Add at least one of:
- Rank-based metrics (Spearman correlation; precision@k for low-usage areas),
- threshold classification (e.g., below 0.20 usage or below state median; report sensitivity/specificity),
- cost-sensitive evaluation (penalize false negatives more heavily),
- a simple "triage simulation" showing how many true low-usage ZCTAs would be flagged under different models.

This would translate the modeling into actionable policy relevance, which is key for JIP.

## 5. Suggestions for Additional Analyses That Would Strengthen the Contribution (Not Strictly Required, But High Value)

### 5.1 Add Stronger "Low-Cost Baseline" Comparators Beyond RUCA

RUCA is indeed low-cost, but it is not the only low-cost feature. If the manuscript's policy takeaway is "typology is a strong baseline; imagery adds little," readers will reasonably ask: strong relative to what?

Consider adding:
- ACS-derived covariates (income, education, age, race/ethnicity, housing tenure), or even a small subset,
- population density,
- distance to metro cores,
- ISP competition proxies if available.

Even one additional "cheap baseline" model would sharpen the paper's policy claim about where imagery sits in the hierarchy of measurement options.

### 5.2 Diagnose When Imagery Helps (Residual Modeling with Interpretation)

You already show a residual map for the RUCA group-mean baseline (Figure 4).

Build on this:
- Are there clusters where RUCA consistently underpredicts or overpredicts usage?
- Do visual features reduce those residuals in specific subregions or RUCA categories?

A targeted "where imagery adds value" analysis could convert the overall negative result into a more nuanced, policy-relevant conditional conclusion.

### 5.3 Consider Within-ZCTA Heterogeneity Features

Averaging the 24 OpenCV features across images may wash out important signals. You could augment the feature set with:
- standard deviation across images,
- quantiles (10th/50th/90th),
- share of images above a "development index" threshold, etc.

This is still low-complexity, but more faithful to heterogeneous ZCTAs. The paper itself notes within-ZCTA heterogeneity as a limitation.

### 5.4 Improve Missingness Handling for ZCTAs Without Imagery

Currently, ZCTAs without imagery are retained with visual features set to zero. Zero is a meaningful value for many image-derived features and may be interpreted as "no edges / no roads," which is not "missing."

At minimum:
- include a binary "imagery_missing" indicator,
- impute missing visual features using training means or a model-based imputer,
- or drop those ZCTAs in visual-only model training and report sensitivity.

## 6. Minor Comments and Editorial Suggestions

**Tighten and refocus the literature review.** The review is wide-ranging and useful, but for JIP you might streamline technical CV citations and expand the "measurement governance" aspect: map accuracy politics, data source accountability, and how measurement choices shape funding distributions.

**Define RUCA codes clearly for non-specialists.** A short mapping of RUCA categories (1-10) to intuitive labels would help, especially because Figure 3 uses numeric codes without labels.

**Report fold composition.** Because spatial CV results are central, include fold counts and basic descriptive stats per fold.

**Explain the "late-fusion stacking" approach.** You mention late-fusion (stacked) models and coefficient norms (RUCA block dominates), but provide little methodological detail. Add a brief description of the stacking procedure and how leakage is avoided.

**Clarify the cap-sensitivity analysis.** The reported cap-sensitivity spatial CV R^2 ranges in Section 3.1.1 appear inconsistent with later contiguity CV results; specify which model and grouping definition those ranges refer to.

**Convert RMSE/MAE into percentage points in the main text.** You note that metrics are in proportion units. Consider reporting "~22 percentage points RMSE" in the narrative so policy readers grasp magnitude.

**Copyediting/format:** ensure consistent use of hyphenation and remove PDF artifacts (if any remain in the final submission). (Some odd hyphenation appears in the extracted text, though this may be preprint formatting rather than true errors.)

## 7. What I Would Look For in a Revised Version

If revised along the lines above, the paper could make a strong JIP contribution as a measurement and validation cautionary case study:
- Clear statement of the policy decision context and what "screening/triage" means in practice.
- Transparent, reproducible imagery sampling protocol and spatial fold construction.
- Consistent, debugged encoding and reporting so the "combined model adds no value" result is unquestionably credible.
- A deeper treatment of the governance implications of using proprietary telemetry and imagery (bias, accountability, transparency).
- At least one policy-oriented evaluation beyond R^2 (ranking or classification for low-usage targeting).

## Bottom Line

This manuscript has a solid core question and a valuable methodological message: spatial validation can overturn optimistic performance claims, and simple typologies can be hard to beat for some broadband measurement tasks.

With clearer study-area definition, tightened and consistent spatial CV reporting, fuller imagery protocol detail, and stronger policy/measurement-governance framing, it could be a publishable and useful contribution to Journal of Information Policy.
