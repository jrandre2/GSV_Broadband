# Peer Review (SR-004)

Review date: 2025-12-28.
Source: synthetic peer review provided by user.
Journal: Journal of Information Policy

## Full review text

Peer review of "Predicting Broadband Usage: A Comparison of Computer Vision and Rural-Urban Typology Machine Learning Models"
index
1) Summary and contribution
This manuscript tests whether Google Street View (GSV) imagery improves prediction of "broadband usage"--the estimated share of residents using speeds >=25/3 Mbps--beyond a rural-urban typology baseline (RUCA) across 264 Nebraska ZIP Code Tabulation Areas (ZCTAs). It extracts a 24-feature handcrafted OpenCV set from GSV images and compares (i) RUCA-only models, (ii) visual-only models, and (iii) combined models, under both a random 80/20 holdout split and several forms of spatial cross-validation. The headline result is a negative one: RUCA-only models are strong on a random holdout (reported best approx R^2 0.40-0.41), visual-only models are somewhat weaker (best approx R^2 0.37), and combining RUCA+visual does not beat RUCA alone. Under the most conservative spatial CV (contiguity/queen clustering), performance collapses (often negative R^2), with large sensitivity to how spatial folds are defined; longitude bands yield substantially more optimistic results than contiguity-based folds. The paper argues RUCA provides a "cheap baseline" for within-region screening, but generalization across distinct geographic regions is weak (including adverse ranking behavior under contiguity CV).
The work has real value as (a) a cautionary note about spatial leakage and evaluation design, and (b) a policy-relevant "negative result" discouraging overconfident claims that street imagery is automatically additive for broadband measurement in visually homogeneous regions.
2) Overall assessment for Journal of Information Policy (fit and significance)
Fit: The topic--measurement and targeting for broadband policy--is squarely within information policy. However, the current manuscript reads primarily as an applied ML benchmarking study with a policy motivation, rather than as an information policy article that uses ML evidence to advance policy arguments about governance, accountability, and decision-making. The paper makes a promising start with "measurement governance considerations" around private telemetry labels, but the policy implications could be developed substantially further to meet JIP's typical expectations (normative clarity, institutional context, and implications for program design).
Significance: The main significance lies in (i) demonstrating that naive random splits can inflate apparent predictive performance for place-based broadband metrics, and (ii) showing that simple typologies may dominate image features in a specific region/label configuration. Both are potentially important and publishable, but only if the manuscript tightens several methodological ambiguities and elevates the policy framing from "motivating context" to "policy contribution."
3) Major strengths
Clear comparison of cheap baselines vs. richer modalities. The RUCA vs. OpenCV vs. combined framing is simple and easy to communicate to policy audiences (Tables 1-2; Results section).
index
Serious engagement with spatial validation. The manuscript correctly emphasizes that random CV can overstate performance under spatial autocorrelation and tests multiple spatial partitioning schemes (Methods 3.4.1; Appendix A).
index
Transparency about limitations and label governance. The discussion of Microsoft telemetry as "ground truth" and concerns about representativeness and normative appropriateness is an important inclusion for information policy (Section 3.3.1).
index
Negative results reported plainly. The paper avoids the common trap of overselling the imagery pipeline; it explicitly states that visual features add limited incremental value in this setting.
index
4) Major issues requiring revision
A. The manuscript's core policy claim needs sharpening: What decision is this meant to support?
The paper alternates between two implied deployment scenarios:
Within-region screening (random holdout split performance approx R^2 0.40): "prioritizing audits within eastern Nebraska."
Cross-region generalization (contiguity CV negative R^2; adverse ranking): "deploying models to new geographic regions."
Both are legitimate--but they are different policy questions and imply different evaluation designs, acceptable error profiles, and governance requirements. Right now, the reader is left with mixed messaging: RUCA is "strong" and "useful," yet policy-relevant metrics under contiguity CV are "random" and even rank-inverted.
What I recommend:
State one primary policy use case in the introduction and carry it through the methods and discussion.
If you want to keep both (which is reasonable), explicitly label them as Use Case 1: within-jurisdiction screening vs. Use Case 2: transfer to a new jurisdiction and avoid blending conclusions. The Appendix D "Interpretation: Within-Region vs Cross-Region Deployment" is a good start, but it appears only at the end; it should be elevated into the main narrative.
For JIP, strengthen the governance implications of each use case: who is accountable for errors, what recourse exists, how a "screening tool" interacts with formal eligibility criteria, and what transparency requirements are appropriate.
B. Outcome validity and "ground truth" governance are not sufficiently resolved for policy interpretation
You appropriately describe the Microsoft dataset as a usage/adoption proxy and note representativeness concerns and lack of an explicit year field (Section 3.3).
index
But the policy narrative still leans on "identifying underserved communities" in a way that risks conflating:
Usage/adoption (who experiences >=25/3 speeds among Microsoft telemetry users)
vs.
Availability / eligibility (where infrastructure is lacking per program rules).
These are related but not interchangeable. A model that predicts low "usage at >=25/3" could be flagging low infrastructure or affordability, device access, digital skills, demographic composition, or platform-specific telemetry bias.
What I recommend:
Tighten terminology throughout: call the target something like "Microsoft-estimated share achieving >=25/3" rather than "broadband usage" (or explicitly define "usage" once and stick to it).
Add a short subsection clarifying how (and whether) this label should inform funding targeting, given that funding often aims at unserved availability, not merely adoption. This is crucial for JIP audiences.
Consider a triangulation sensitivity: even a modest comparison between Microsoft usage and an ACS-based broadband subscription/adoption measure at ZCTA (if available), or FCC availability at a comparable geography, would help readers interpret what the model is "really" picking up. You do compare RUCA to ACS socioeconomic predictors (Appendix B), but that does not validate the target construct.
index
C. Inconsistencies/ambiguities in the dataset and sampling pipeline undermine interpretability
There are several places where the described pipeline seems internally inconsistent:
Total images vs. cap: You report 7,619 images overall and then say that for modeling you "cap extraction at 10 images per ZCTA" selected alphabetically (Section 3.2.1).
index
It is unclear whether (i) you extracted features from all 7,619 and then averaged over a capped subset, or (ii) you extracted features only from the capped subset. This matters: using ~10 images vs. ~29 images per ZCTA changes signal-to-noise.
Cap sensitivity analysis appears incorrect: The manuscript states, "Cap-sensitivity analyses using the RUCA categorical model... across 5, 10, 20, and all images yield R^2 from -0.28 to -0.27" (Section 3.2.1).
index
RUCA models do not use images, so image caps should not affect RUCA performance. This reads like either a copy-editing mistake (you meant "visual-only model") or a deeper reproducibility issue.
Handling ZCTAs without imagery is inconsistent: early text says the 3 ZCTAs without imagery are excluded from visual-only/combined models (Section 3.1), but later says that in spatial CV all 264 are used and missing visual features are set to zero.
index
Then the Results claim all models use the same fixed holdout split (Section 4.6). These cannot all be simultaneously true.
What I recommend:
Provide a single, unambiguous "Data pipeline" diagram or step-by-step description:
How many GSV points per ZCTA were requested?
How many returned valid panoramas?
How many unique panoramas (duplicates matter)?
Exactly how many images per ZCTA entered modeling?
Fix the cap-sensitivity statement and run it on the visual models (and/or combined). If you already ran it, report it correctly (ideally as a small figure/table showing performance vs. number of images). If you did not, it is a key robustness check given your conclusion that imagery adds limited value.
Handle missing imagery in a way that does not introduce artificial structure:
Prefer dropping the 3 ZCTAs for all models (including RUCA) when comparing modalities, or impute visual features using fold-wise means plus a missing-indicator, rather than setting to zero (which can create out-of-range values after scaling).
D. Spatial CV design: the "canonical" contiguity split is extremely imbalanced and conflates spatial generalization with category support
Your contiguity-based folds are highly imbalanced: Fold 1 contains 121 ZCTAs and 114 of 135 metro ZCTAs, while other folds have 31-38 (Appendix C).
index
This creates a severe distribution shift in RUCA composition across folds, which you acknowledge. Under such a split, models are not merely asked to generalize to new geography; they are asked to predict RUCA categories that are scarcely present in training when certain folds are held out. For one-hot RUCA models, this can become an "out-of-support" problem rather than a meaningful test of transfer.
This matters because your strongest policy claim is that contiguity-based CV is the "most conservative" and therefore canonical. I agree it is conservative, but I'm not convinced it is the most policy-relevant without a clearer deployment scenario and without addressing the fold imbalance.
What I recommend:
Report fold-level results (not just mean +/- SD) for the contiguity CV so readers can see whether one fold drives the negative mean R^2. You already provide an explanation narrative; show the numbers.
Add at least one spatial CV scheme that is conservative and more balanced. For example:
Spatial blocking with constraints on fold size (blockCV-style),
Buffered CV (hold out a region plus a distance buffer),
Cluster counts > 5 to reduce the "metro in one fold" problem (e.g., 8-10 folds), if feasible.
Interpret negative R^2 carefully: in scikit-learn, R^2 is benchmarked against the test-fold mean. A model that predicts well conditional on categories seen in training can still get negative R^2 under extreme distribution shifts. Your Appendix D ranking inversion result is interesting, but the interpretation should separate "model fails" from "evaluation split induced category shift."
index
E. The "combined models don't improve RUCA" conclusion needs a more diagnostic analysis
It is plausible that RUCA subsumes most of what your OpenCV features capture (built-environment proxies). But to make the "no incremental value" claim convincing, the paper should show why.
Also, Table 1 reports identical performance for "Visual only ElasticNet" and "Combined ElasticNet" (same R^2, RMSE, MAE), which is suspicious and could indicate an implementation issue or reporting error.
index
What I recommend:
Verify and correct Table 1 combined ElasticNet results if needed; if they are truly identical, explain why (e.g., RUCA coefficients shrunk to ~0 due to regularization or preprocessing).
Add an incremental predictive value analysis:
Compute delta R^2 (or delta MAE) of adding visual features to RUCA under the same validation scheme, with uncertainty (bootstrap on the holdout or repeated splits).
Alternatively, residualize: fit RUCA-only, then test whether visual features predict RUCA residuals.
Add a compact interpretability section:
Feature importance/permutation importance for the visual-only model,
Correlations between RUCA category means and each visual feature,
A short discussion of whether the OpenCV features are essentially "urbanicity detectors," in which case it is unsurprising that RUCA dominates.
This would strengthen both the technical story and the policy story ("don't pay for images if the features merely replicate typology").
F. The manuscript has presentation/structure problems that must be fixed prior to journal consideration
Two abstracts appear at the beginning (a short abstract and then a longer "Abstract" again).
index
JIP will require a single coherent abstract.
The extended abstract contains more results and metrics than the short abstract, and the two appear to emphasize slightly different performance summaries (e.g., "best RUCA around 0.13" vs. specific values later). Harmonize and ensure consistency with Appendix A.
Several methods/results statements read like notes (e.g., reproducibility bullet lists) rather than final narrative prose (Section 4.8).
index
This is fine for a preprint but should be revised for journal style.
5) Suggestions to better align the paper with JIP's policy emphasis
This is the single biggest "publishability" lever for the manuscript.
Make the measurement-governance section central, not peripheral. Section 3.3.1 is a good start; expand it into a policy argument about:
legitimacy of private telemetry in public decision-making,
representativeness and disparate impact,
transparency/contestability of model outputs,
auditability (what would an affected community do if the model flags them incorrectly?).
Connect the evaluation design to accountability. Your core technical point (spatial CV scheme changes conclusions) has a direct policy analogue: if agencies use models evaluated with optimistic splits, they may systematically misprioritize communities. Spell this out explicitly and propose reporting norms (you already recommend multiple schemes; elevate this as a policy recommendation).
Clarify the "cheap baseline" logic in policy terms. If RUCA is already available and performs as well as more complex pipelines (within-region), then:
what is the appropriate role of ML at all?
is the best policy advice "use RUCA as a screening heuristic" or "use RUCA to allocate audit budgets," etc.?
what harms occur if policymakers overinterpret R^2=0.40 from a random split?
Be explicit about what "underserved" means in your label. Your Precision@20% analysis (Appendix D) is useful, but it needs clear justification for why "bottom quintile" is a meaningful policy cutoff and how it maps (or does not map) to program thresholds.
index
6) Additional analyses that would materially strengthen the manuscript (recommended)
If you have bandwidth for one "major add-on," I would prioritize the following:
Image-count sensitivity for the visual model (not RUCA): show performance vs. {5, 10, 20, all} images per ZCTA under both holdout and at least one spatial CV scheme. This directly addresses whether the "imagery adds limited value" result is an artifact of under-sampling images.
Ablation: RUCA vs. ACS vs. RUCA+ACS under holdout: You only report ACS comparison under contiguity spatial CV (Appendix B).
index
For policy readers, it matters whether a small set of socioeconomic variables beats RUCA or images within-region as well.
A simple "coordinates-only" baseline (lat/long, or longitude alone): given your own observation that Nebraska has a strong east-west gradient and longitude-band CV is less pessimistic, include a coordinate baseline to demonstrate how much of the predictive signal is essentially a spatial trend. This would also clarify what RUCA is doing.
Fold-wise diagnostics: show test-fold means, RUCA composition, and prediction bias per fold for contiguity CV. Appendix C explains the mechanism; showing a plot/table would make the argument much more compelling.
index
7) Minor comments and editorial suggestions
Terminology: "broadband usage," "adoption," and "accessing >=25/3" are used somewhat interchangeably. Tighten to one term and define it precisely once.
Figures:
Figure 1 (study area) is helpful but should ensure readability of boundaries and labels at print size.
index
Figure 2 (fold map) is important for the spatial CV story; consider annotating fold sizes directly on the map or in the caption.
index
Figure 3 (RUCA distribution boxplot) is useful; consider adding sample counts per RUCA category because some categories may be sparse.
index
Tables: Include N (observations) used for each model family if it differs (264 vs 261) and clarify whether the same holdout indices were used across feature sets.
Reproducibility: You list software versions and hyperparameter grids (Section 4.8), which is excellent.
index
For publication, you should provide (i) a repository link, (ii) code for generating ZCTA features, (iii) stored panorama IDs or metadata needed for reproducibility under changing GSV imagery.
8) Recommendation
Major revision (potentially "revise and resubmit"): the question is worthwhile, the negative result is credible in principle, and the spatial validation emphasis is a valuable contribution. But several core methodological ambiguities (image cap statement, missing imagery handling, sample comparability across models, suspicious identical ElasticNet results, and the implications of highly imbalanced contiguity folds) must be resolved before the conclusions can be relied upon. Strengthening the policy framing and governance analysis would also be essential for Journal of Information Policy.
