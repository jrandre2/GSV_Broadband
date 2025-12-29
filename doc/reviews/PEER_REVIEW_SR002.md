# Peer Review Intake (SR-002)

Status: Current.
Review date: 2025-12-28.
Source: Synthetic peer review provided by user; latest manuscript.
Full text: doc/logs/peer_review_sr002.md.

## Manuscript summary (reviewer)

- Question: does GSV imagery improve broadband usage prediction beyond RUCA typology?
- Data: 264 ZCTAs in eastern Nebraska; OpenCV features + pretrained CNN embeddings (no fine-tuning).
- Results: holdout favors RUCA-only; spatial CV drops performance sharply; combined does not exceed RUCA.

## Overall evaluation / fit

- Fit for JIP: good policy relevance, but more transparency and clearer policy use case needed.
- Recommendation: major revision / revise-and-resubmit.
- Emphasis: spatial CV findings are a key contribution; paper reads as a concise ML benchmark.

## Major strengths

- Policy-relevant framing and negative-result message.
- Clear RUCA vs visual vs combined comparisons.
- Spatial validation included.
- Metrics reported in readable tables.

## Major issues (priority)

- Clarify predictive (non-causal) framing and avoid causal interpretation.
- Justify ZIP/ZCTA unit and policy actionability at that resolution.
- Clarify imagery sampling and the 10-image cap; add descriptive stats and sensitivity.
- Document leakage controls for PCA/scaling and show fold-specific preprocessing.
- Fully specify spatial CV design (fold construction, parameters, map).
- Diagnose combined-model underperformance and block-level contributions.
- Add RUCA group-mean baseline and interpretability diagnostics.
- Expand usage-target validity and policy implications.
- Provide reproducibility details (feature list, PCA components, hyperparameters, software).

## Suggested analyses (optional)

- Sensitivity to image quantity (5/10/20/all), and use all images with equal ZIP weighting.
- Policy cost comparison (RUCA vs GSV pipeline costs).
- Out-of-region validation.
- Feature-block ablations (OpenCV vs CNN vs both).

## Minor comments and editorial fixes

- Standardize ZIP vs ZCTA terminology; clarify units for RMSE/MAE.
- Reframe numeric RUCA baseline as naive encoding or drop it.
- Fix LiDAR footnote formatting and reference hyphenation artifacts.
- Explain RUCA2 omission with a brief test/metric.
- Add GSV terms-of-use and IRB/exemption statement.

## Integration notes

- Use data_work/diagnostics outputs as the metric source of truth.
- Track responses in doc/reviews/PEER_REVIEW_RESPONSE_SR002.md.
