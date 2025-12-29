# Peer Review (SR-002)

Review date: 2025-12-28.
Source: synthetic peer review provided by user.

Reviewer report (Journal of Information Policy)
Manuscript summary
The manuscript asks whether Google Street View (GSV) imagery improves prediction of broadband "usage" (estimated % using >=25/3 Mbps) beyond a rural-urban typology baseline. Using 264 ZIP code tabulation areas (ZCTAs) in eastern Nebraska, the author extracts (i) OpenCV-style handcrafted image features and (ii) pretrained CNN embeddings (ResNet50/VGG16/InceptionV3, no fine-tuning), aggregates them to the ZIP level, and compares RUCA-only, visual-only, and combined models across linear/regularized regression and tree ensembles. On a fixed random 80/20 split, the strongest RUCA-only models reach test R^2 ~= 0.40, the strongest visual-only models reach ~= 0.37, and combined models do not exceed the RUCA baseline; however, spatial cross-validation with nested tuning sharply reduces performance (RUCA ~= 0.13; visual/combined near 0 or negative), suggesting limited geographic generalization.
index
Overall evaluation / fit for Journal of Information Policy
The core question-what low-cost, scalable signals can support digital divide targeting-fits Journal of Information Policy's interest in measurement, governance, and policy-relevant evidence about broadband inequalities.
index
The paper's most policy-relevant contribution is arguably not the "visual vs. typology" horse race per se, but the demonstration that standard random holdouts may substantially overstate performance compared with spatially separated validation in this context.
index
That said, in its current form the manuscript reads like a concise ML benchmarking note. For JIP, it likely needs (1) substantially more methodological transparency and reproducibility, (2) clearer articulation of the policy decision context where a ZIP-level predictor is actionable, and (3) a tighter conceptual framing distinguishing prediction from explanation/causality.
index
Recommendation: Major revision / revise-and-resubmit.
Major strengths
Policy-relevant framing and negative result is informative. The manuscript explicitly tests whether a costly modality (imagery) adds value beyond a simple typology baseline, and finds it often does not-an important "don't over-engineer" message for policy analytics.
index
Direct comparison across feature sets and model classes. The side-by-side RUCA-only vs. visual-only vs. combined design is clear and allows a clean incremental-value question.
index
Inclusion of spatial validation is a major plus. The spatial cross-validation results (near-zero/negative for visual models; RUCA around 0.13) are exactly the kind of robustness check that many applied ML-for-policy papers omit.
index
Clear reporting of key test metrics. Tables are readable and include R^2/RMSE/MAE for comparability.
index
Major issues that need to be addressed
1. Clarify the inferential claim: "predicts" vs "explains"
The title and some language in the manuscript can be read as claims about determinants of broadband usage ("what predicts"), but the design is correlational and focused on out-of-sample prediction.
index
Why this matters for JIP: Policy audiences often interpret "predictors" as levers. RUCA is not a lever; it is a typology proxy. Imagery features are not levers either. The paper should be explicit that:
The models are for measurement/targeting, not for identifying causal drivers.
"Predictive signal" != "policy intervention target."
Concrete revisions
Adjust wording throughout: "predict" -> "forecast" or "statistically predict," and explicitly disavow causal interpretation in the Introduction and Discussion.
Consider retitling to something like: "Predicting broadband usage from RUCA typology and street imagery: evidence from eastern Nebraska."
2. The unit of analysis (ZIP/ZCTA) and policy actionability needs justification
The study is at ZIP code / ZCTA level, using RUCA ZIP disaggregation and Microsoft "U.S. Broadband Usage Percentages" at ZIP level.
index
JIP readers will ask: What policy decision is made at ZIP level today? BEAD and many broadband planning efforts are increasingly location- or block-level; ZIP-level targeting can be blunt.
Concrete revisions
Add a short subsection explaining the intended use case:
Is the goal triage/prioritization for deeper auditing?
Is it "screening" to identify likely low-usage areas when other data are missing?
Discuss the consequences of ZIP aggregation (rural ZCTAs can be huge; within-ZIP heterogeneity can be large).
3. Street View sampling methodology is under-specified and internally hard to reconcile
The manuscript reports:
Sampling an initial manifest of 500 structures per ZIP (100-1000 m^2).
index
Collecting 7,612 images across 261 of 264 ZIPs, with four cardinal images per building.
index
Using "up to 10 images per ZIP" in modeling.
index
These points leave several ambiguities:
What is a "full sample" per ZIP? (500 structures? a smaller target?)
index
If four images are captured per building, 7,612 images implies ~1,903 building locations total-about ~7 locations per ZIP on average for 261 ZIPs. That seems low relative to the "500 structures per ZIP" manifest and needs explanation (coverage limitations? strict date filter? API costs?).
index
Why cap to 10 images per ZIP if the average ZIP apparently has ~29 images? If the goal is to keep each ZIP equally weighted, there are more statistically efficient ways (see below).
Concrete revisions
Add descriptive stats and a figure/table:
Number of buildings sampled per ZIP (mean/median/IQR; min/max).
Number of images per ZIP (and per RUCA category).
Missingness: which 3 ZIPs have no imagery and why?
index
Justify the 10-image cap and test sensitivity:
Re-run with 5/10/20/all images per ZIP.
Consider an alternative to "cap at 10" that preserves equal ZIP weighting while using all images:
Compute ZIP-level aggregates using all available images but weight ZIPs equally in modeling (most regression/tree methods already treat each row equally once you aggregate, so this may simply mean: aggregate using all images, not a cap).
Or bootstrap images within ZIP to estimate uncertainty in ZIP-level feature estimates.
4. Potential preprocessing leakage: PCA and scaling must be fit within training folds
You reduce CNN embeddings with PCA and then model at ZIP level.
index
PCA is learned from data. If PCA is fit using all images (or all ZIPs) prior to train/test split, it introduces information leakage that can inflate holdout performance. Even though PCA is unsupervised, it can still leak structure from the test set.
Concrete revisions (critical)
Explicitly state (and implement) a pipeline where:
Train/test split occurs at ZIP level first.
Any learned preprocessing (PCA, scaling, feature selection) is fit only on training data and applied to test data.
In spatial nested CV, preprocessing is refit within each training fold.
Add a short "leakage control" paragraph in Methods and, ideally, a reproducible pipeline diagram.
5. Spatial cross-validation design needs full specification
The manuscript reports spatial CV with nested tuning and gives mean +/- SD R^2.
index
This is promising, but the evaluation hinges on the spatial splitting strategy.
Key missing details
What constitutes a "spatial fold"? (k-means on coordinates, blocking grid, county-based folds, buffered leave-one-cluster-out, etc.)
How many folds/repeats?
What geography is used (ZIP centroid? population-weighted centroid)?
How are neighboring ZIPs prevented from being split across train/test in the same fold (if at all)?
Concrete revisions
Add a subsection: Spatial cross-validation protocol.
Provide parameters: number of folds, block size (or clustering method), random seeds, and a map illustrating folds.
Report not only mean +/- SD but also the distribution or at least min/max across folds, because SDs reported are very large relative to means (e.g., 0.130 +/- 0.316).
index
6. The "combined models" result needs diagnosis
Combined models underperform RUCA-only (and sometimes look similar to visual-only, e.g., ElasticNet with identical metrics).
index
This pattern could occur for multiple reasons:
RUCA encoding in combined pipelines might be inconsistent (e.g., treated as numeric instead of categorical/one-hot).
Regularization might zero-out RUCA features if scaling/penalty choices favor the high-dimensional visual block.
Noise from high-dimensional visual features may swamp signal in small n = 264.
For trees, irrelevant features can degrade split quality in small samples, especially with default max_features behavior.
Concrete revisions
Ensure RUCA is consistently treated as categorical in all relevant models (especially combined).
Add a small diagnostic:
For ElasticNet: show coefficient norms for RUCA vs visual blocks, or report whether RUCA coefficients are non-zero.
For trees: report permutation importance or SHAP summary at least at the block level (RUCA block vs visual block).
Consider a simple stacked/late-fusion approach:
Train RUCA-only and visual-only models, then fit a meta-model on their predictions (within CV). This often outperforms naive feature concatenation when modalities differ in dimensionality and noise.
7. Baselines and interpretability: RUCA-only performance should be contextualized
A one-hot ridge on RUCA achieves ~0.40 on the random holdout.
index
But RUCA is a coarse typology; JIP readers will want to know:
Is the model essentially learning RUCA-category means (i.e., the group mean baseline)?
How much within-RUCA variation exists, and where does the model fail?
Concrete revisions
Add a baseline: predict each ZIP by the mean usage of its RUCA category computed from training data (this is the intuitive "typology lookup table").
Add an interpretability/diagnostic figure:
Boxplots of broadband usage by RUCA category (in the sample).
Map of residuals (where does RUCA systematically under/over-predict?).
This will make the "policy message" clearer: RUCA is strong because usage differs sharply by RUCA categories-if that is what is happening.
8. Target variable validity and policy interpretation needs expansion
You use Microsoft Research's ZIP-level "broadband usage percentages," interpreted as an adoption/usage proxy.
index
The manuscript notes this as a limitation, but for JIP it deserves more front-and-center discussion because policy targeting depends on what is being measured.
Concrete revisions
Provide details: year(s) of the usage estimates, update frequency (if known), and any documented biases (e.g., telemetry skews toward Microsoft ecosystem users).
Be explicit about how "usage >=25/3" relates to:
Adoption vs availability,
Device ecosystem effects,
Potential socioeconomic confounding.
Consider adding a paragraph: Implications of modeling usage (not availability) for broadband grants and mapping.
9. Reproducibility expectations for JIP
Right now, many critical implementation details are omitted (exact feature list, embedding dimensionality, PCA components retained, hyperparameter grids, etc.).
index
Concrete revisions
Provide:
A GitHub/OSF repository (or supplemental appendix) with code, parameter grids, and a reproducible pipeline.
A "data availability" statement clarifying what can be shared (likely not raw GSV images, but derived features and ZIP-level aggregates could be).
Software versions and compute environment.
Suggestions for additional analyses (optional but would strengthen the paper)
These are not all required, but one or two would substantially strengthen the contribution:
Sensitivity to image quantity and sampling bias
Re-estimate models using different caps (5/10/20/all) and report whether the "imagery adds little" conclusion is robust.
index
A "policy cost" comparison
Since the policy motivation is cost-effective targeting, provide a brief comparison:
RUCA data cost/time vs GSV pipeline cost/time (API calls, processing).
If imagery yields marginal gains (or none), quantify the tradeoff.
Out-of-region validation
Even a small extension-e.g., train on eastern Nebraska and test on a different part of Nebraska (or a neighboring state) if feasible-would align with the generalization concerns shown by spatial CV.
index
Feature-block ablations
Separate "OpenCV handcrafted" vs "CNN embeddings" vs "both" to identify where the (limited) visual signal is coming from.
index
Minor comments and editorial fixes
Define and standardize terms: you use "ZIP codes (ZCTAs)"-consider a brief clarification early on and then use one term consistently.
index
Units for RMSE/MAE: clarify whether the target is in [0,1] or [0,100] and interpret RMSE in percentage points.
index
RUCA treatment: the "Linear" RUCA baseline appears to treat RUCA as numeric; given RUCA codes are categorical/nominal, it may mislead. Consider dropping or reframing it explicitly as a "naive numeric coding" baseline.
index
Footnote formatting: the LiDAR footnote appears malformed ("LiDAR1" / "1a remote sensing method..."). Clean up numbering and formatting.
index
Reference hygiene: several references include URL line-break artifacts/hyphenation; ensure consistent formatting for final submission.
index
Explain why RUCA2 was dropped: you note RUCA2 adds little; briefly report a metric or describe the test you ran.
index
Ethics / terms of use: add a short statement about use of Google Street View imagery consistent with Google's terms and any IRB/exemption status (even if exempt).
index
Bottom line
The paper's central finding-typology-based models provide a strong, low-cost baseline and imagery adds limited incremental value in this setting, especially under spatial validation-is potentially valuable for policy-facing audiences.
index
To reach Journal of Information Policy standards, the manuscript needs more transparency around sampling and preprocessing (especially leakage control), a fully specified spatial CV design, and a clearer articulation of how ZIP-level predictive modeling informs real policy targeting decisions.
