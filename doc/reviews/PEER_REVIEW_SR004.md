# Peer Review Intake (SR-004)

Status: Superseded by SR-005.
Review date: 2025-12-28.
Source: Synthetic peer review provided by user; Journal of Information Policy framing.
Full text: doc/logs/peer_review_sr004.md.

## Manuscript summary (reviewer)

- Tests whether GSV OpenCV features add predictive value over RUCA across 264 Nebraska ZCTAs.
- Compares RUCA-only, visual-only, and combined models under holdout and spatial CV.
- Finds strong random holdout performance but weak/negative contiguity-based spatial CV; combined adds little.

## Overall evaluation / fit

- Fit: within JIP scope, but policy framing needs stronger governance argumentation.
- Recommendation: major revision / revise-and-resubmit.
- Significance: highlights spatial leakage risk and typology dominance in a homogeneous region.

## Major strengths

- Clear RUCA vs visual vs combined framing for policy audiences.
- Serious engagement with spatial validation and sensitivity.
- Transparent acknowledgment of label governance limits.
- Negative results presented plainly.

## Major issues (priority)

- Clarify primary policy use case(s) and governance implications.
- Tighten target terminology (usage/adoption vs availability) and policy relevance.
- Resolve imagery sampling/cap/missing-coverage inconsistencies; add a clear pipeline description.
- Address contiguity CV imbalance; report fold-level results and consider balanced alternatives.
- Diagnose combined-model incremental value; verify identical ElasticNet metrics.
- Fix presentation issues (duplicate abstract; draft-like prose sections).

## Suggested analyses (optional)

- Visual-model image-count sensitivity (5/10/20/all) under holdout and spatial CV.
- RUCA vs ACS vs RUCA+ACS under holdout.
- Coordinates-only baseline.
- Fold-wise diagnostics (means, composition, bias) for contiguity CV.

## Minor comments and editorial fixes

- Standardize target terminology.
- Add fold sizes to spatial CV map; add RUCA counts to boxplot; include N per model family.
- Improve figure readability and expand reproducibility pointers (repo link, feature-gen code, panorama metadata).

## Integration notes

- Use data_work/diagnostics outputs as the canonical metric source.
- Track responses in doc/reviews/PEER_REVIEW_RESPONSE_SR004.md.
