# Peer Review (SR-001)

Review date: 2025-12-28.
Source: synthetic peer review provided by user.
Note: ASCII-normalized from original text.

Peer review of the attached preprint
Manuscript: What Predicts Broadband Usage? A Comparison of Computer Vision and Rural-Urban Typology Machine Learning Models (Jesse Andrews; dated 2025-12-28).
index
Summary of what the paper does
The paper asks whether Google Street View (GSV) imagery can predict ZIP-level broadband usage better than a simple rural-urban typology (RUCA). The study uses 264 ZIP codes (ZCTAs) in eastern Nebraska, downloads 7,612 GSV images, engineers visual features (OpenCV-style handcrafted features + pretrained CNN embeddings reduced via PCA), and compares models trained on (i) RUCA-only, (ii) visual-only, and (iii) RUCA+visual feature sets. The target is broadband usage from a Microsoft Research "U.S. Broadband Usage Percentages" dataset, defined as estimated percent using internet at >= 25/3 Mbps. Models are evaluated on a single fixed 80/20 split and reported with test R2/RMSE/MAE. The headline result is that RUCA-only ensembles reach ~0.39 test R2, while the best visual-only model reaches ~0.30, and the combined models do not exceed the RUCA baseline.
index
This is a useful "negative result" style paper: it's practically relevant, and it usefully warns that "more complex data" (street imagery) may not beat cheap typologies in visually homogeneous regions.
Strengths
Clear comparative framing. The manuscript is organized around a concrete question: Do GSV-derived visual signals add predictive value beyond a rural-urban typology?
index
Pragmatic, policy-relevant motivation. The "principle of efficiency" (try simpler/cheaper data sources first) is a sensible applied takeaway in broadband investment contexts.
index
Use of multiple model families. Comparing linear, ElasticNet, and tree ensembles is a reasonable first sweep.
index
High coverage of ZIPs with imagery. The paper reports imagery for 261/264 ZIP codes (98.9%), which is better coverage than many GSV studies achieve in rural areas.
index
Major issues to address before this is publication-ready
1) Construct validity: what exactly is being predicted, and how does that map to "broadband investment"?
The target is described as "broadband usage" derived from Microsoft telemetry ("percentage... accessing the internet at or above 25/3 Mbps").
index
But much of the motivation and discussion reads like the goal is to infer infrastructure gaps / availability.
These are related but not identical constructs:
Usage/adoption is shaped by: affordability, digital skills, device access, age, education, perceived utility, etc.
Availability is shaped more by: infrastructure, provider presence, terrain, rights-of-way, density economics, etc.
RUCA will correlate strongly with both, but possibly for different reasons. If the policy application is infrastructure buildout targeting, a model of "usage" may steer money toward areas with low adoption for socioeconomic reasons rather than unserved infrastructure.
Actionable fix:
Be explicit and consistent about whether this paper is about adoption/usage vs availability/infrastructure. If you intend an infrastructure story, consider adding (even as a robustness check) a second target closer to "availability" (if obtainable) or reframe the conclusion as: "RUCA is a stronger predictor of usage in this region than facade-level imagery."
index
2) RUCA encoding and the interpretation of "non-linear relationships"
The manuscript argues that because a linear RUCA baseline has R2 ~= 0.144 while ensemble models reach R2 ~= 0.392, this indicates "strong non-linear relationships" between RUCA typology and broadband usage.
index
This interpretation may be incorrect or at least overstated depending on how RUCA was encoded:
RUCA codes are categorical typology labels. If you feed them as a single numeric column (e.g., 1,2,...,10), a linear model is mis-specified because it assumes an ordinal linear trend.
A tree ensemble on a single categorical-ish numeric feature can effectively act like a lookup table / step function, producing large gains without revealing deep "non-linear structure."
What I'd expect if RUCA is properly treated as categorical:
A linear model with one-hot encoding can already match "lookup table" behavior (category means). If you run:
LinearRegression(one_hot(RUCA))
you may find performance much closer to the tree ensembles, undermining the "non-linear unlock" narrative.
Actionable fixes (high priority):
State explicitly whether RUCA is treated as categorical (one-hot/target encoding) or numeric.
Add a baseline: one-hot RUCA + linear regression (or ridge) and compare to ensembles.
If RUCA has many decimal subclasses, consider grouping/regularizing or using an encoding appropriate to your policy interpretation.
index
3) Evaluation design: a single random 80/20 split is not enough (and is likely optimistic due to spatial autocorrelation)
The paper reports performance on a fixed 80/20 holdout split with a single seed.
index
With only 264 ZIPs, the test set is roughly ~53 observations. That makes R2 noisy, and one split can easily favor one feature set.
More importantly, ZIP codes are spatially embedded; broadband usage and built environment features have spatial autocorrelation. A random split may place neighboring ZIPs in train and test, inflating apparent generalization.
Actionable fixes (high priority):
Report repeated splits (e.g., 30-100 random splits) or K-fold cross-validation at the ZIP level and show mean +/- std (or confidence intervals) of R2/RMSE/MAE.
Include a spatial CV or grouped CV (e.g., hold out by county/commuting zone/lat-long clustering). This matters a lot for the claim "typology beats imagery" in an applied setting.
Report whether your split was stratified by RUCA (it probably wasn't). If RUCA categories are rare, one split can be misleading.
Without these, the conclusions may be directionally right but not statistically/empirically secure.
index
4) Potential leakage / pipeline hygiene (especially PCA)
You state you extract CNN embeddings and then reduce dimensionality using PCA.
index
A key question: Was PCA fit only on the training set (and then applied to test), or fit on the full dataset before splitting?
Even unsupervised transforms can leak test-distribution information. The correct pattern is a single scikit-learn Pipeline where scaling/PCA are fit within each training fold/split only.
Actionable fix:
Add a short paragraph clarifying the pipeline order and leakage safeguards. If you did it correctly, say so explicitly; if not, rerun with a proper pipeline and update Table 1.
index
5) Confusing/inconsistent description of the image sampling intensity
Three statements do not line up cleanly:
You report 7,612 images across 261 ZIPs.
index
You say "For modeling, we use up to 10 images per ZIP."
index
Later, you discuss "an average of fewer than 30 images per ZIP."
index
Numerically, 7,612 / 261 ~= 29.2 images/ZIP, which matches the "<30" statement. That suggests "10 images per ZIP" may actually mean 10 locations/buildings per ZIP (each with 4 cardinal-direction frames -> up to ~40 images/ZIP), or something similar.
Actionable fix:
Clarify precisely:
what the unit of sampling is (building vs image),
the targeted sample size per ZIP (buildings? images?),
and what subset is actually used in modeling.
This matters because the paper's central explanation for limited visual performance is "data sparsity," and right now readers can't tell what "sparsity" means operationally.
index
6) Fairness of the RUCA vs visual comparison
RUCA-only models have one/few features; visual models likely have many (OpenCV features + CNN PCs + mean/std aggregation).
index
With N=264, high-dimensional feature sets can easily underperform without careful regularization and tuning.
Also, your combined models perform worse than RUCA-only (e.g., RUCA-only Extra Trees R2 ~= 0.392 vs combined Extra Trees R2 ~= 0.279).
index
In principle, adding predictive features shouldn't reliably harm performance if the model is tuned/regularized well - performance drops often indicate:
overfitting due to high dimensionality,
insufficient hyperparameter tuning,
scaling/encoding issues,
or a pipeline bug (e.g., RUCA not actually included, or features misaligned).
Actionable fixes:
Report hyperparameter strategy. If "defaults," say so; but then consider tuning (nested CV).
For combined models, try:
stronger regularization (ridge/elastic net with CV),
limiting tree depth / min_samples_leaf,
feature subsampling,
or a two-stage residual approach (see suggestions below).
Confirm RUCA is actually being concatenated in the combined feature matrix (the identical ElasticNet R2 for visual-only and combined is a mild "smoke signal" to double-check).
index
7) Table 1 has suspiciously identical metrics across different models
In Table 1, several different models share exactly the same R2/RMSE/MAE to three decimals (e.g., RUCA-only Random Forest / Extra Trees / Gradient Boosting all show identical 0.392 / 0.228 / 0.175).
index
This can happen, but it is uncommon. It raises a possibility of:
heavy rounding masking differences,
reuse of predictions,
or an implementation issue.
Actionable fixes:
Report more precision (e.g., 4-5 decimals), or show distributions across resamples.
Add a quick sanity check statement: "We verified distinct predictions across model classes."
Important but secondary issues / clarifications
A) Data provenance and citation gaps
Key datasets/tools should be directly cited with stable references:
Microsoft "U.S. Broadband Usage Percentages" dataset (currently described, but not clearly cited as a dataset artifact).
index
Google Street View Static API (and Metadata API if used for date filtering).
"Google Buildings Footprint dataset" (name/licensing/version needs a precise citation).
index
Readers need to know: dataset version, time coverage, and any known biases.
B) Temporal alignment
You filter imagery to "within the last decade," use RUCA derived from 2010-era commuting patterns, and use Microsoft usage estimates (year unspecified in the manuscript).
index
If these data sources come from different years, measurement mismatch can dampen the visual signal.
Actionable fix: Add a short timeline table: RUCA year; imagery capture year distribution; Microsoft usage year.
C) Unit of geography: ZIP vs ZCTA
You use the terms "ZIP codes" and "ZCTAs" interchangeably.
index
These are not identical constructs. It's fine to work at this resolution, but you should be explicit about:
which geometry you're using,
how RUCA ZIP file corresponds to your unit,
and how the Microsoft dataset defines ZIP.
D) Generalization claims
The conclusion emphasizes "visually homogeneous regions" like Nebraska.
index
That's plausible, but currently asserted rather than demonstrated. A simple way to back this up:
quantify within-region variance of key visual features,
show clustering of embeddings,
or show representative images across RUCA categories.
Concrete analyses that would materially strengthen the paper (in priority order)
Repeated evaluation + uncertainty
Repeated random splits OR K-fold CV with mean+/-std for each model-feature set.
Add a spatial/block CV variant.
RUCA encoding experiment
Compare: numeric RUCA vs one-hot RUCA vs spline/ordinal encoding.
Revisit the "non-linear relationships" claim accordingly.
Baseline: RUCA group mean predictor
A simple predictor that outputs the mean broadband usage for each RUCA code (fit on train) gives an interpretable benchmark. Tree ensembles on a single feature may be approximating exactly this.
Incremental value conditional on RUCA
Evaluate whether visual features help within RUCA strata:
compute performance separately per RUCA category (where sample sizes permit), or
model residuals: y - f(RUCA) predicted using visual features.
This directly answers: "Do images refine targeting beyond typology?"
Ablation of visual features
OpenCV-only vs CNN-embedding-only vs combined, to learn which visual signals (if any) matter.
Error analysis
Identify ZIPs with largest residuals under RUCA-only models; inspect whether visual features help those cases.
Minor comments and editorial suggestions
Consider shortening/streamlining the literature review: it is extensive relative to the brevity of the methods/results section; readers will want more methodological transparency given the paper's empirical claim.
index
Tighten terminology:
"deep learning" vs "pretrained embeddings without fine-tuning,"
"broadband usage" vs "estimated usage >= 25/3 Mbps."
Add a brief "Limitations" subsection that explicitly covers:
telemetry bias of the target,
GSV coverage bias,
spatial dependence,
and generalization limits beyond Nebraska.
index
Reproducibility & transparency checklist (what I would expect in the revision)
Exact ZIP/ZCTA list and definition of "eastern Nebraska" selection rule.
index
Train/test split policy (seed, stratification, spatial constraints).
index
Full feature specification (names, counts, PCA component count).
index
Pipeline details (scaling, PCA fit scope, leakage prevention).
index
Hyperparameters (or tuning method) for each model.
index
Data availability statement (what can be shared vs restricted by API terms).
Overall recommendation
Recommendation: Major revision.
The core idea is strong and the negative result is valuable, but the current evidence is not yet robust enough to support the stronger interpretive claims (especially about "non-linear RUCA signal" and "combined models not improving"), largely because of encoding ambiguity, single-split evaluation, and unclear image sampling description. Addressing the points above - especially proper RUCA encoding, repeated/spatial validation, and pipeline clarity - would make this a solid, publishable applied methods paper.
